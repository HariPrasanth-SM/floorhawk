import unittest
from cumulative_evidence import pack, decision


class CumulativeEvidenceTests(unittest.TestCase):
    def test_target_priority_and_explicit_omissions(self):
        rows = [{'id': str(i), 'class': 'door', 'text': 'context' * 30}
                for i in range(10)]
        local = {'task': {'target': 'window'},
                 'evidence': [{'id': 'selected', 'class': 'window'}],
                 'cumulative_evidence': {'evidence': rows, 'outputs': []}}
        selected, context = pack(local, {}, budget=200)
        self.assertEqual(selected[0]['id'], 'selected')
        self.assertGreater(context['omitted_regions'], 0)
        self.assertFalse(context['complete_context'])

    def test_no_reference_or_gold_packing(self):
        local = {'expected': 'PRIVATE', 'grade': True,
                 'cumulative_evidence': {'evidence': [
                     {'id': 'one', 'text': 'Room', 'reference': 'PRIVATE'}],
                     'outputs': []}}
        self.assertNotIn('PRIVATE', str(pack(local, {})))

    def test_keep_model_provenance_and_distinct_ids(self):
        rows = [{'id': 'ocr:1', 'origin_model': 'ocr', 'text': 'W1'},
                {'id': 'custom:1', 'origin_model': 'custom_yolo', 'class': 'window'}]
        selected, _ = pack({'cumulative_evidence': {'evidence': rows}}, {})
        self.assertEqual(len(selected), 2)
        self.assertEqual({x['origin_model'] for x in selected}, {'ocr', 'custom_yolo'})

    def test_abstention_not_overwritten_by_local(self):
        self.assertEqual(decision({'answer': 7}, {'status': 'abstained'})['selected'], 'abstained')

    def test_failure_preserves_local_explicitly(self):
        d = decision({'answer': 7}, {'status': 'provider_error'})
        self.assertEqual(d['selected'], 'local')
        self.assertTrue(d['recommended_review'])

    def test_agreement_not_proof(self):
        d = decision({'answer': 7, 'unit': 'count'},
                     {'status': 'success', 'answer': 7, 'unit': 'count'})
        self.assertIn('not independent proof', d['reason'])


if __name__ == '__main__':
    unittest.main()
