import unittest
from scripts.agile_score import classify,summary,paired,stats

class AgileScoringTests(unittest.TestCase):
 def gold(self,typ='count',answer=3,unit='count'):
  return {'type':typ,'answer':answer,'unit':unit,'question':'How many windows?'}
 def test_missing_not_execution_success(self):
  self.assertEqual(classify(self.gold(),None)['outcome'],'Not recorded')
  self.assertEqual(classify(self.gold(),{'status':'success','answer':2,'unit':'count'})['outcome'],'Incorrect')
  self.assertEqual(classify(self.gold(),{'status':'abstained','answer':None})['outcome'],'Abstained')
 def test_text_no_substring_or_free_form_credit(self):
  g=self.gold('text','IFC4',None);g['question']='What IFC schema?'
  self.assertEqual(classify(g,{'status':'success','answer':'ifc 4'})['outcome'],'Text correct')
  self.assertEqual(classify(g,{'status':'success','answer':'IFC4 and IFC2x3'})['outcome'],'Text incorrect')
  g['answer']='A long property narrative'
  self.assertEqual(classify(g,{'status':'success','answer':g['answer']})['outcome'],'Answered but ungraded')
 def test_same_manifest_missing_stays_denominator(self):
  good=classify(self.gold(),{'status':'success','answer':3,'unit':'count'});missing=classify(self.gold(),None)
  rows=[{'sample_id':'a','drawing_id':'one','type':'count','local':good,'hybrid':good},{'sample_id':'b','drawing_id':'two','type':'count','local':missing,'hybrid':good}]
  s=summary(rows,'local');self.assertEqual(s['total'],2);self.assertEqual(s['numeric_correct_all'],.5);self.assertEqual(s['outcomes']['Not recorded'],1)
  p=paired(rows,'local','hybrid');self.assertEqual(p['numeric_recorded_in_both_n'],1);self.assertEqual(p['missing_either_n'],1);self.assertEqual(p['states'],{'unchanged_correct':1})
 def test_timing_missing_is_not_zero(self):
  self.assertEqual(stats([None,-1,0,2])['n'],2);self.assertEqual(stats([])['median'],None)
if __name__=='__main__':unittest.main()
