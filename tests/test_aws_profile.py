import unittest

from jawsome.AWS_profile import AWS_profile

class TestConfig(unittest.TestCase):

    def test_create_kwargs(self):
        a=['param1','param2']
        b = {
            "service_name": {
                "function_name": {
                    "random_name": [
                        {'junk':'junk','param1':'toto','junk1':'junk1'},
                        {'junka':'junka','param1':'tata','junka1':'junka1'},
                        {"junkb": "junkb","param2": "fefe","junkb1": "junkb1",},
                    ]
                }
            }
        }
        solution = [
                {'param1':'toto'},
                {'param1':'tata'},
                {'param2':'fefe'},
                {'param1':'toto','param2':'fefe'},
                {'param1':'tata','param2':'fefe'}
            ]
        kwargs = AWS_profile.create_kwargs(params_names=a, artifacts=b)
        self.assertEqual(kwargs, solution)