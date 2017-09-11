from rest_framework import serializers


class TestInitialData:
    """
    Reference github issue #5345.

    Tests that the .initial_data the ListSerializer is updating the
    initial_data of it's child serializer as it is iterating.

    This test is done by checking that:

    1. The length of the .initial_data is equal to the number of items included
       in the test case's input_data, and

    2. Test that the .initial_data passed to the .validate() function is a
       dict.

    (Note that the assert statements are included in the .validate() method as
    this is where we want to look at the data to verify it's behaviour.)

    """

    def setup(self):
        class TestSerializer(serializers.Serializer):
            number = serializers.IntegerField()

            def validate(self, attrs):
                assert len(self.initial_data) == 1
                assert isinstance(self.initial_data, dict)
                return attrs

        self.Serializer = TestSerializer

    def test_initial_data(self):

        input_data = {"number": 1}
        serializer = self.Serializer(data=input_data)
        serializer.is_valid()

        input_data = [{"number": 1}, {"number": 2}]
        list_serializer = self.Serializer(data=input_data, many=True)
        list_serializer.is_valid()
