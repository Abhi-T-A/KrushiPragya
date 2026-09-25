from app.services.weather_provider import (
    WeatherProvider,
    ForecastProvider,
    WeatherProviderError,
    OpenWeatherMapProvider,
    MockWeatherProvider,
    get_weather_provider,
)
from app.services.weather_service import WeatherService
from app.services.weather_rule_engine import (
    WeatherMetrics,
    AdvisoryMatch,
    evaluate_rule,
    evaluate_rules_for_crop,
    normalize_crop_name,
)
from app.services.weather_aggregation_service import (
    get_weather_metrics,
    is_observation_cloudy,
)
from app.services.weather_advisory_service import (
    get_weather_advisories,
    get_weather_advisory_bundle,
    WeatherAdvisoryResult,
    VillageNotFoundError,
    CropNotFoundError,
)
from app.services.weather_forecast_service import WeatherForecastService
from app.services.forecast_aggregation_service import (
    ForecastAggregationService,
    is_forecast_item_cloudy,
)
from app.services.forecast_advisory_service import (
    ForecastAdvisoryService,
    ForecastAdvisoryResult,
    UnsupportedRule,
)
from app.services.farmer_advisory_service import (
    FarmerAdvisoryService,
    get_farmer_advisory_service,
    OLLAMA_ADVISORY_SYSTEM_PROMPT,
)
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    SUPPORTED_CROPS,
    DiseaseDetectionError,
    UnsupportedCropError,
    EmptyImageError,
    InvalidImageError,
    ModelNotFoundError,
    InvalidCheckpointError,
)
from app.services.farmer_profile_service import (
    FarmerProfileService,
    FarmerProfileError,
    FarmerProfileNotFoundError,
    FarmerProfileAlreadyExistsError,
)
from app.services.farmer_crop_service import (
    FarmerCropService,
    FarmerCropError,
    FarmerNotFoundError,
    InactiveCropError,
    FarmerCropAlreadyExistsError,
    FarmerCropNotFoundError,
)
from app.services.crop_report_service import (
    CropReportService,
    CropReportError,
    CropReportNotFoundError,
)
from app.services.crop_report_storage_service import (
    CropReportStorageService,
    CropReportStorageError,
    UnsupportedImageTypeError,
    ImageSizeLimitExceededError,
    StorageServiceError,
    get_crop_report_storage_service,
)
from app.services.crop_report_diagnosis_service import (
    CropReportDiagnosisService,
    CropReportDiagnosisServiceError,
    CropReportImageNotFoundError,
    get_crop_report_diagnosis_service,
)
from app.services.llm_provider import (
    LLMProvider,
    GroqProvider,
    OllamaProvider,
    LLMProviderError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMResponseError,
    get_llm_provider,
)



__all__ = [
    "WeatherProvider",
    "ForecastProvider",
    "WeatherProviderError",
    "OpenWeatherMapProvider",
    "MockWeatherProvider",
    "get_weather_provider",
    "WeatherService",
    "WeatherMetrics",
    "AdvisoryMatch",
    "evaluate_rule",
    "evaluate_rules_for_crop",
    "normalize_crop_name",
    "get_weather_metrics",
    "is_observation_cloudy",
    "get_weather_advisories",
    "get_weather_advisory_bundle",
    "WeatherAdvisoryResult",
    "VillageNotFoundError",
    "CropNotFoundError",
    "WeatherForecastService",
    "ForecastAggregationService",
    "is_forecast_item_cloudy",
    "ForecastAdvisoryService",
    "ForecastAdvisoryResult",
    "UnsupportedRule",
    "FarmerAdvisoryService",
    "DiseaseDetectionService",
    "SUPPORTED_CROPS",
    "DiseaseDetectionError",
    "UnsupportedCropError",
    "EmptyImageError",
    "InvalidImageError",
    "ModelNotFoundError",
    "InvalidCheckpointError",
    "FarmerProfileService",
    "FarmerProfileError",
    "FarmerProfileNotFoundError",
    "FarmerProfileAlreadyExistsError",
    "FarmerCropService",
    "FarmerCropError",
    "FarmerNotFoundError",
    "InactiveCropError",
    "FarmerCropAlreadyExistsError",
    "FarmerCropNotFoundError",
    "CropReportService",
    "CropReportError",
    "CropReportNotFoundError",
    "CropReportStorageService",
    "CropReportStorageError",
    "UnsupportedImageTypeError",
    "ImageSizeLimitExceededError",
    "StorageServiceError",
    "get_crop_report_storage_service",
    "CropReportDiagnosisService",
    "CropReportDiagnosisServiceError",
    "CropReportImageNotFoundError",
    "get_crop_report_diagnosis_service",
    "LLMProvider",
    "GroqProvider",
    "OllamaProvider",
    "LLMProviderError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "LLMResponseError",
    "get_llm_provider",
    "get_farmer_advisory_service",
    "OLLAMA_ADVISORY_SYSTEM_PROMPT",
]
