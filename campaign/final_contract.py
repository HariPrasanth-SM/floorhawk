"""Answer-free final worker protocol; usable without Modal/model imports."""
def validate_questions(rows):
 if not isinstance(rows,list)or not 1<=len(rows)<=128:raise ValueError('Bounded question batch required')
 for row in rows:
  if not isinstance(row,dict)or set(row)!={'sample_id','question'}or not isinstance(row['sample_id'],str)or len(row['sample_id'])>160 or not isinstance(row['question'],str)or not 1<=len(row['question'])<=3000:raise ValueError('Only bounded question identity/text permitted; no labels or references')
 if len({r['sample_id']for r in rows})!=len(rows):raise ValueError('Duplicate question identity')
