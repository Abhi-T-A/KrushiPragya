"""SQLAlchemy database models for KrushiPragya."""
from app.models.village import Village
from app.models.user_profile import UserProfile
from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.weather_observation import WeatherObservation
from app.models.advisory_rule import AdvisoryRule

from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.role import Role, UserRole
from app.models.expert_verification import ExpertVerificationRequest, CommunityCorroboration
from app.models.marketplace import ProduceListing, BuyerOffer
from app.models.government import (
    GovernmentScheme,
    SchemeApplication,
    SchemeSource,
    SchemeCrawlRun,
    SchemeSourceDocument,
    SchemeUserState,
)
from app.market.models.market_source import MarketDataSource
from app.market.models.market import Market
from app.market.models.market_mapping import MarketCropMapping
from app.market.models.market_price import MarketPriceRecord
from app.market.models.market_follow import FarmerMarketFollow

__all__ = [
    "Village",
    "UserProfile",
    "Crop",
    "FarmerCrop",
    "CropReport",
    "CropReportDiagnosis",
    "WeatherObservation",
    "AdvisoryRule",
    "Role",
    "UserRole",
    "ExpertVerificationRequest",
    "CommunityCorroboration",
    "ProduceListing",
    "BuyerOffer",
    "GovernmentScheme",
    "SchemeApplication",
    "SchemeSource",
    "SchemeCrawlRun",
    "SchemeSourceDocument",
    "SchemeUserState",
    "MarketDataSource",
    "Market",
    "MarketCropMapping",
    "MarketPriceRecord",
    "FarmerMarketFollow",
]
