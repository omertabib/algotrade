import pytest
from datetime import datetime
from models.dto.AlpacaTick import AlpacaTick
from data_providers.AlpacaDataProvider import AlpacaDataProvider
from models.schemas.NormalizedTick import NormalizedTick

class TestAlpacaDataProvider:

    def test_transform_data_success(self):
        """בדיקת מסלול הצלחה - המרה תקינה של DTO ל-Schema"""
        # 1. Arrange
        dto = AlpacaTick(
            T="t", S="TSLA", i=123, x="V", p=170.5, s=100,
            t="2024-03-20T10:00:00.000Z", c=["@"]
        )

        # 2. Act
        result = AlpacaDataProvider.transform_data(dto)

        # 3. Assert
        assert result.error is None
        assert result.value is not None
        assert result.value.symbol == "TSLA"
        assert result.value.price == 170.5
        assert isinstance(result.value.timestamp, int)
        # ודוא שהזמן הפך למילי-שניות (13 ספרות בדרך כלל)
        assert len(str(result.value.timestamp)) >= 13

    def test_transform_data_zero_price_error(self):
        """בדיקת ולידציה - מחיר 0 צריך להחזיר Result עם שגיאה"""
        # 1. Arrange
        dto = AlpacaTick(
            T="t", S="AAPL", i=456, x="V", p=0.0, s=10,
            t="2024-03-20T10:00:00Z", c=["@"]
        )

        # 2. Act
        result = AlpacaDataProvider.transform_data(dto)

        # 3. Assert
        assert result.value is None
        assert result.error is not None
        assert result.error.code == 100
        assert "Price cannot be 0" in result.error.message