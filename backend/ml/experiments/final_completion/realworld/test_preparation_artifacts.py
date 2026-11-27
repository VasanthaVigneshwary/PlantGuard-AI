"""Fast, read-only consistency tests for the prepared real-world artifacts."""
import csv,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
def csvr(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
class PreparedArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classes=json.loads((HERE/'classes.json').read_text(encoding='utf-8'))['classes']
        cls.ft=csvr(HERE/'field_train.csv'); cls.fv=csvr(HERE/'field_val.csv')
        cls.pv=csvr(HERE/'plantvillage_train_filtered.csv'); cls.protected=csvr(HERE/'protected_plantdoc_evaluation.csv')
    def test_approved_38_class_order_and_coverage(self):
        source=json.loads((ROOT/'backend/ml/models/classes.json').read_text(encoding='utf-8'))['classes']
        self.assertEqual(self.classes,source); self.assertEqual(len(self.classes),38); self.assertEqual(len(set(self.classes)),38)
        self.assertEqual({r['class_name'] for r in self.pv},set(self.classes))
    def test_manifest_indices_match_mapping(self):
        for row in self.ft+self.fv+self.pv:
            self.assertEqual(self.classes[int(row['class_index'])],row['class_name'])
    def test_field_train_validation_hash_and_group_separation(self):
        self.assertFalse({r['sha256'] for r in self.ft}&{r['sha256'] for r in self.fv})
        self.assertFalse({r['group_id'] for r in self.ft}&{r['group_id'] for r in self.fv})
    def test_protected_plantdoc_hashes_excluded(self):
        protected={r['sha256'] for r in self.protected}
        self.assertEqual(len(protected),123)
        self.assertFalse(protected&({r['sha256'] for r in self.ft}|{r['sha256'] for r in self.fv}|{r['sha256'] for r in self.pv}))
    def test_pv_test_split_not_in_any_training_manifest(self):
        test=csvr(ROOT/'backend/ml/experiments/stage3_preflight/plantvillage_test.csv')
        test_members={r['member'] for r in test}; test_hashes={r['sha256'] for r in test}
        self.assertFalse(test_members&{r['archive_member'] for r in self.pv})
        self.assertFalse(test_hashes&{r['sha256'] for r in self.pv})
        self.assertTrue(all(r['split']=='train' for r in csvr(ROOT/'backend/ml/experiments/stage3_preflight/plantvillage_train.csv')))
        self.assertTrue(all(r['class_name'] in self.classes for r in test))
    def test_split_sizes_and_counts(self):
        summary=json.loads((HERE/'split_summary.json').read_text(encoding='utf-8'))
        self.assertEqual((len(self.ft),len(self.fv)),(1069,268))
        self.assertEqual(summary['field_train_val_group_overlap'],0)
        self.assertEqual(summary['plantvillage_train_filtered'],37993)
    def test_audit_and_inventory_preserve_partial_sources_as_excluded(self):
        audit=csvr(HERE/'leakage_audit.csv'); inv=json.loads((HERE/'source_inventory.json').read_text(encoding='utf-8'))
        self.assertEqual(inv['PlantDoc_partial_extract']['usable_for_training'],0)
        self.assertTrue(any(r['decision']=='excluded' for r in audit))
        self.assertEqual(inv['backend_uploads']['usable_for_training'],0)
    def test_unlabeled_local_images_do_not_match_protected_evaluation(self):
        audit=csvr(HERE/'local_unusable_source_overlap_audit.csv')
        self.assertFalse(any(r['matched_source']=='PlantDoc protected evaluation' for r in audit))
if __name__=='__main__':unittest.main(verbosity=2)
