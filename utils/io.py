# coding=utf-8
import pickle, json


def read_table(pathfile):
 if pathfile.is_file():
   lines = pathfile.read_text(encoding='utf-8').split('\n')
   lines = [[i.strip() for i in l.split(';')] for l in lines if l.strip()]
   return lines
 return []

def write_table(pathfile, table):
 raw = '\n'.join(';'.join(i.strip() for i in line) for line in table if line)
 pathfile.write_text(raw, encoding='utf-8')



def read_order(pathfile, format='json'):
  # -> dict
  if format in ('pkl', 'pickle'):
    with pathfile.open('rb') as f:
      return pickle.load(f)

  elif format == 'json':
    with pathfile.open('r', encoding='utf8') as f:
      return json.load(f)

  raise ValueError('format must be json|pkl|pickle')

def save_order(pathfile, obj, format='json'):
  if format in ('pkl', 'pickle'):
    with pathfile.open('wb') as f:
      return pickle.dump(obj, f)

  elif format == 'json':
    with pathfile.open('w', encoding='utf8') as f:
      return json.dump(obj, f, ensure_ascii=False)

  raise ValueError('format must be json|pkl|pickle')







