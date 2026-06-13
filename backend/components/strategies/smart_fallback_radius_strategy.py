# backend/components/strategies/smart_fallback_radius_strategy.py

from __future__ import annotations

from typing import Any

from backend.kernel.contracts.base_execution_strategy import BaseExecutionStrategy
from backend.kernel.models import GeoResponse, QueryIR


class SmartFallbackRadiusStrategy(BaseExecutionStrategy):
    """
    Execution strategy wrapper with automatic radius expansion fallback.

    This plugin wraps another execution strategy. It does not depend on
    StrategyRegistry internals and does not modify the kernel.

    Important:
    - It preserves response.metadata["strategy"] from the base strategy.
    - It stores its own information under wrapper-specific metadata keys.
    """

    fallback_ratios = [1.0, 1.8, 2.8, 4.0]

    def __init__(
        self,
        base_strategy: BaseExecutionStrategy,
        min_results: int = 1,
        default_radius_m: int = 3000,
    ) -> None:
        self.base_strategy = base_strategy
        self.min_results = min_results
        self.default_radius_m = default_radius_m

    @property
    def name(self) -> str:
        return "smart_fallback_radius_strategy"

    def can_handle(self, query_ir: QueryIR) -> bool:
        return self.base_strategy.can_handle(query_ir)

    async def execute(
        self,
        query_ir: QueryIR,
        dataset_id: str | None = None,
        **kwargs: Any,
    ) -> GeoResponse:
        original_radius = self._resolve_original_radius(query_ir)
        attempts: list[dict[str, Any]] = []
        last_response: GeoResponse | None = None

        for index, ratio in enumerate(self.fallback_ratios):
            attempted_radius = int(original_radius * ratio)

            adjusted_ir = self._with_radius(
                query_ir=query_ir,
                radius_m=attempted_radius,
            )

            response = await self.base_strategy.execute(
                adjusted_ir,
                dataset_id=dataset_id,
                **kwargs,
            )
            last_response = response

            target_count = self._count_target_features(response)
            satisfactory = target_count >= self.min_results

            attempts.append(
                {
                    "ratio": ratio,
                    "failed": not satisfactory,
                    "target_results": target_count,
                    "total_features": len(response.features),
                    "attempted_radius_m": attempted_radius,
                }
            )

            if satisfactory:
                self._attach_fallback_metadata(
                    response=response,
                    attempts=attempts,
                    used=index > 0,
                    original_radius=original_radius,
                    effective_radius=attempted_radius,
                )

                if index > 0:
                    response.warnings.append(
                        "در شعاع اولیه نتیجه کافی یافت نشد؛ "
                        f"شعاع جستجو به صورت خودکار تا {attempted_radius} متر افزایش یافت."
                    )

                return response

        if last_response is not None:
            max_radius = (
                attempts[-1]["attempted_radius_m"] if attempts else original_radius
            )

            self._attach_fallback_metadata(
                response=last_response,
                attempts=attempts,
                used=True,
                original_radius=original_radius,
                effective_radius=max_radius,
            )

            last_response.warnings.append(
                "حتی با افزایش خودکار شعاع نیز نتیجه کافی یافت نشد."
            )
            return last_response

        response = await self.base_strategy.execute(
            query_ir,
            dataset_id=dataset_id,
            **kwargs,
        )

        self._attach_fallback_metadata(
            response=response,
            attempts=attempts,
            used=False,
            original_radius=original_radius,
            effective_radius=original_radius,
        )
        return response

    def _resolve_original_radius(self, query_ir: QueryIR) -> int:
        """
        Resolve radius from metadata first because DatasetGeodataStrategy uses
        metadata['radius_meters'] for provider search.
        """
        metadata_radius = query_ir.metadata.get("radius_meters")
        if metadata_radius:
            return int(float(metadata_radius))

        constraints_radius = getattr(query_ir.constraints, "radius_m", None)
        if constraints_radius:
            return int(float(constraints_radius))

        return self.default_radius_m

    def _with_radius(self, query_ir: QueryIR, radius_m: int) -> QueryIR:
        """
        Clone QueryIR with a new radius.

        DatasetGeodataStrategy currently reads radius from metadata['radius_meters'],
        so this plugin updates both metadata and constraints.
        """
        updated_metadata = {
            **query_ir.metadata,
            "radius_meters": radius_m,
            "effective_radius_m": radius_m,
        }

        updated_constraints = query_ir.constraints.model_copy(
            update={"radius_m": radius_m}
        )

        return query_ir.model_copy(
            update={
                "metadata": updated_metadata,
                "constraints": updated_constraints,
            }
        )

    def _count_target_features(self, response: GeoResponse) -> int:
        """
        Count target features and ignore anchor/reference features if they exist.
        """
        return len(
            [
                feature
                for feature in response.features
                if feature.metadata.get("role") != "anchor"
            ]
        )

    def _attach_fallback_metadata(
        self,
        *,
        response: GeoResponse,
        attempts: list[dict[str, Any]],
        used: bool,
        original_radius: int,
        effective_radius: int,
    ) -> None:
        """
        Attach wrapper metadata without overriding the base strategy metadata.

        response.metadata["strategy"] must remain owned by the base strategy,
        because existing tests and API behavior depend on it.
        """
        response.metadata["wrapper_strategy"] = self.name
        response.metadata["base_strategy"] = self.base_strategy.name
        response.metadata["radius_fallback_attempts"] = attempts
        response.metadata["radius_fallback_used"] = used
        response.metadata["original_radius_m"] = original_radius
        response.metadata["effective_radius_m"] = effective_radius
