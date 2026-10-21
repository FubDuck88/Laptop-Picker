import unittest
from source_audit import audit_allit_offer


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.offer = {'id':'o1','source_id':'allit','seller':'ALL IT','source_product_id':'1',
                      'variant_id':'2','url':'https://www.allithypermarket.com.my/products/test?variant=2',
                      'price_sen':399900,'availability':'unknown'}
        self.config = {'manufacturer_part_number':'TEST-1','cpu_model':'Intel Core i7-13620H',
                       'memory':{'capacity_gb':16},'evidence':{
                           'identity_scope':{'raw_value':'Product 1, variant 2, SKU TEST-1'},
                           'cpu_model':{'raw_value':'Intel Core i7-13620H'},
                           'memory':{'raw_value':'6GB GDDR6 / 16GB DDR4'}}}
        self.product = {'id':1,'title':'Laptop TEST-1','body_html':'<p>Intel® Core™ i7-13620H</p><p>Graphics: 6GB GDDR6</p><p>RAM: 16GB DDR4</p>',
                        'variants':[{'id':2,'sku':'TEST-1','price':'3999.00'}]}
        self.html = '<script type="application/ld+json">{"@type":"Offer","itemCondition":"https://schema.org/NewCondition"}</script>'

    def test_raw_evidence_survives_trademarks_and_multiple_labeled_values(self):
        self.assertTrue(audit_allit_offer(self.offer,self.config,self.product,self.html)['passed'])

    def test_different_price_wrong_variant_missing_condition_or_changed_facts_fail(self):
        self.product['variants'][0]['price'] = '3888'
        self.assertFalse(audit_allit_offer(self.offer,self.config,self.product,self.html)['checks']['public_price'])
        self.product['variants'][0]['id'] = 3
        self.assertFalse(audit_allit_offer(self.offer,self.config,self.product,self.html)['checks']['variant_id'])
        self.assertFalse(audit_allit_offer(self.offer,self.config,self.product,'<html></html>')['checks']['new_condition'])
        self.product['body_html'] = '<p>Different CPU and RAM</p>'
        self.assertFalse(audit_allit_offer(self.offer,self.config,self.product,self.html)['checks']['known_field_evidence'])
