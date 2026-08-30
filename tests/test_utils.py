import unittest

from jawsome.utils import get_json_string_keys

class TestUtils(unittest.TestCase):

    def test_get_json_string_keys(self):
        test1 = {'dynamodbstreams': {'list_streams': {'Streams': [{'StreamArn': 'arn:aws:dynamodb:us-east-2:324081753546:table/test/stream/2026-08-30T15:59:14.957', 'StreamLabel': '2026-08-30T15:59:14.957', 'TableName': 'test'}]}}}
        test2 = {'dynamodb': {'describe_endpoints': {'Endpoints': [{'Address': 'dynamodb.us-east-2.amazonaws.com', 'CachePeriodInMinutes': 1440}]}, 'list_tables': {'TableNames': ['Alerts', 'Users']}}}

        test1_res = ["StreamArn", "StreamLabel", "TableName"]
        test2_res = ["Address", "CachePeriodInMinutes", "TableNames"]
        self.assertListEqual(get_json_string_keys(test1), test1_res)
        self.assertListEqual(get_json_string_keys(test2), test2_res)
