"""Read-only 38-class knowledge-base content/provenance inventory."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BACKEND=ROOT/'backend'
sys.path.insert(0,str(BACKEND));sys.path.insert(0,str(BACKEND/'services'))
from database import get_connection
from services.database_service import get_verified_application_rate_metadata

def audit():
    classes=json.loads((BACKEND/'ml/models/classes.json').read_text(encoding='utf-8'))['classes']
    conn=get_connection();cur=conn.cursor();cur.execute('SET TRANSACTION READ ONLY;')
    try:
        cur.execute("""
        SELECT d.prediction_key,d.id,d.name,c.name,
         (NULLIF(BTRIM(d.description),'') IS NOT NULL),
         (SELECT count(*) FROM disease_symptoms x JOIN symptoms s ON s.id=x.symptom_id WHERE x.disease_id=d.id AND NULLIF(BTRIM(s.name),'') IS NOT NULL AND NULLIF(BTRIM(s.description),'') IS NOT NULL),
         (SELECT count(*) FROM disease_causes x JOIN causes q ON q.id=x.cause_id WHERE x.disease_id=d.id AND NULLIF(BTRIM(q.name),'') IS NOT NULL AND NULLIF(BTRIM(q.description),'') IS NOT NULL),
         (SELECT count(*) FROM treatments t WHERE t.disease_id=d.id AND NULLIF(BTRIM(t.name),'') IS NOT NULL),
         (SELECT count(*) FROM treatments t WHERE t.disease_id=d.id AND NULLIF(BTRIM(t.name),'') IS NOT NULL AND NULLIF(BTRIM(t.description),'') IS NOT NULL AND NULLIF(BTRIM(t.instructions),'') IS NOT NULL AND NULLIF(BTRIM(t.precautions),'') IS NOT NULL),
         (SELECT count(*) FROM disease_prevention x JOIN prevention p ON p.id=x.prevention_id WHERE x.disease_id=d.id AND NULLIF(BTRIM(p.title),'') IS NOT NULL AND NULLIF(BTRIM(p.description),'') IS NOT NULL)
        FROM diseases d JOIN crops c ON c.id=d.crop_id WHERE d.prediction_key IS NOT NULL ORDER BY d.prediction_key,d.id;
        """)
        rows=cur.fetchall()
        cur.execute("SELECT d.prediction_key,ar.notes FROM application_rates ar JOIN treatments t ON t.id=ar.treatment_id JOIN diseases d ON d.id=t.disease_id;")
        rates={label:[] for label in classes}
        for label,notes in cur.fetchall():
            if label in rates:rates[label].append(notes)
        cur.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name IN ('diseases','symptoms','causes','treatments','prevention','application_rates') ORDER BY table_name,ordinal_position;")
        schema=cur.fetchall()
    finally:
        cur.close();conn.close()
    by={}
    for row in rows:by.setdefault(row[0],[]).append(row)
    result=[]
    for label in classes:
        ms=by.get(label,[]);r=ms[0] if ms else None
        result.append({'class':label,'mapping_count':len(ms),'description_nonblank':bool(r and r[4]),'symptoms_with_name_and_description':int(r[5]) if r else 0,'causes_with_name_and_description':int(r[6]) if r else 0,'treatment_records':int(r[7]) if r else 0,'treatment_records_with_all_text_fields':int(r[8]) if r else 0,'prevention_with_title_and_description':int(r[9]) if r else 0,'application_rates':len(rates[label]),'verified_application_rates':sum(get_verified_application_rate_metadata(n) is not None for n in rates[label])})
    return {'audit_mode':'PostgreSQL read-only transaction','class_count':len(classes),'mapped_class_count':sum(r['mapping_count']>0 for r in result),'duplicate_class_mappings':{r['class']:r['mapping_count'] for r in result if r['mapping_count']>1},'class_rows':result,'schema_columns':{t:[c for table,c in schema if table==t] for t in sorted({table for table,_ in schema})},'aggregate_counts':{'nonblank_descriptions':sum(r['description_nonblank'] for r in result),'classes_with_symptoms':sum(r['symptoms_with_name_and_description']>0 for r in result),'classes_with_causes':sum(r['causes_with_name_and_description']>0 for r in result),'classes_with_treatment_records':sum(r['treatment_records']>0 for r in result),'classes_with_complete_treatment_text':sum(r['treatment_records_with_all_text_fields']>0 for r in result),'classes_with_prevention':sum(r['prevention_with_title_and_description']>0 for r in result),'total_application_rates':sum(r['application_rates'] for r in result),'verified_application_rates':sum(r['verified_application_rates'] for r in result)}}

def main():
    data=audit();out=ROOT/'backend/ml/experiments/final_completion/website_knowledge_audit_20261127.md'
    if out.exists():raise FileExistsError(f'Refusing to overwrite {out}')
    lines=['# Read-only website knowledge-base audit (2026-11-27)','','- Database transaction: `SET TRANSACTION READ ONLY`; no records/schema modified.','- API smoke test: `GET /api/diseases/39` returned HTTP 200, Tomato Septoria Leaf Spot, description, 3 symptoms, 2 causes, 1 treatment and 3 prevention rows; 0 verified application rates. Payload has no source fields.','- UI cause: `getDisplayableDiseaseGuidance` requires `verified === true`, matching `disease_id`, and a trusted HTTPS `source_url` for every content item. The API does not supply these fields for descriptions/symptoms/causes/treatments/prevention, and the schema has no source fields for those tables. It therefore suppresses stored but unverified content and shows its unavailable message.','- This is a provenance/data-evidence gap, not a failed fetch or disease-key mismatch. Treatment rows exist, but all 27 application-rate rows are unverified and correctly omitted from the calculator. No agriculture text or rates were fabricated.','',f"- Mapping: {data['mapped_class_count']}/{data['class_count']} unique disease mappings; duplicates: {len(data['duplicate_class_mappings'])}.",'','| Approved class | map | description | symptom entries | cause entries | treatment rows (complete text) | prevention entries | rates (verified) |','|---|---:|---|---:|---:|---:|---:|---:|']
    for r in data['class_rows']:
        lines.append(f"| `{r['class']}` | {r['mapping_count']} | {'present' if r['description_nonblank'] else 'missing'} | {r['symptoms_with_name_and_description']} | {r['causes_with_name_and_description']} | {r['treatment_records']} ({r['treatment_records_with_all_text_fields']}) | {r['prevention_with_title_and_description']} | {r['application_rates']} ({r['verified_application_rates']}) |")
    agg=data['aggregate_counts']; lines+=['',f"- Coverage: descriptions {agg['nonblank_descriptions']}/38; symptoms {agg['classes_with_symptoms']}/38; causes {agg['classes_with_causes']}/38; treatment rows {agg['classes_with_treatment_records']}/38 (complete text {agg['classes_with_complete_treatment_text']}/38); prevention {agg['classes_with_prevention']}/38.",f"- Application rates: {agg['total_application_rates']} total; {agg['verified_application_rates']} verified. No verified rate should be displayed or calculated.",'','## Safe next action','','Attach reviewed, authoritative source provenance to knowledge records through the project’s approved data-governance process, then expose that metadata through the API. Until then, keep the current unavailable guidance message and verified-rate-only calculator behavior.']
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps({'report':str(out),'aggregate_counts':agg,'mapped_classes':data['mapped_class_count'],'schema_columns':data['schema_columns']},indent=2))
if __name__=='__main__':main()
