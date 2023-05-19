from django.test import TestCase
from mtdcontroller.models import MTD_action

# Create your tests here.
class MTD_action_test(TestCase):
    def setUp(self):
        MTD_action.objects.create(mtd_action ='nomtd')

    
    def test_MTD_created(self):
        action = MTD_action.objects.get(mtd_action='nomtd')
        print(action)
        self.assertEqual(action.mtd_action, 'nomtd')