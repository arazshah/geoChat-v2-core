# backend/kernel/registries/dataset_provider_registry.py

from __future__ import annotations

from backend.kernel.contracts.base_geodata_provider import BaseGeodataProvider
from backend.kernel.models.datasource import DataSourceDescriptor
from backend.kernel.registries.base_registry import BaseRegistry


class DatasetProviderRegistry(BaseRegistry[BaseGeodataProvider]):
    """
    Registry for geodata providers by dataset id.

    Example:
    - 'urmia' -> UrmiaSQLiteProvider
    - 'tehran' -> TehranPostGISProvider
    - 'gee_ndvi' -> GoogleEarthEngineProvider
    """

    def register_provider(
        self,
        dataset_id: str,
        provider: BaseGeodataProvider,
        *,
        overwrite: bool = False,
    ) -> None:
        self.register(dataset_id, provider, overwrite=overwrite)

    def get_provider(self, dataset_id: str) -> BaseGeodataProvider | None:
        return self.get(dataset_id)

    def require_provider(self, dataset_id: str) -> BaseGeodataProvider:
        return self.require(dataset_id)

    def get_descriptor(self, dataset_id: str) -> DataSourceDescriptor:
        return self.require_provider(dataset_id).get_descriptor()

    def list_descriptors(self) -> list[DataSourceDescriptor]:
        return [provider.get_descriptor() for provider in self.list_items()]
