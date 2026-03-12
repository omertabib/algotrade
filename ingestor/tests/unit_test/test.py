from ...data_providers.AlpacaDataProvider import AlpacaDataProvider
from ...models.dto.AlpacaTick import AlpacaTick


class TestAlpacaDataProvider:

    def test_transform_data_success(self):
        """Success path test - valid conversion from DTO to Schema"""
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
        # Verify timestamp was converted to milliseconds (usually 13 digits)
        assert len(str(result.value.timestamp)) >= 13

    def test_transform_data_zero_price_error(self):
        """Validation test - price of 0 should return Result with error"""
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