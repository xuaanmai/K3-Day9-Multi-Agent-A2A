import json
import glob
import re

def verify():
    errors = []
    evidence_pattern = re.compile(r'^(order:|item:|payment:|seller:|policy:)')

    files = sorted(glob.glob('output/EC_*.json'))
    if len(files) != 50:
        errors.append(f"Expected 50 files in output/, found {len(files)}")

    for p in files:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        
        case_id = d.get('case_id')
        
        # 1. Assessment
        ass = d.get('assessment', {})
        if ass.get('case_status') not in ['action_required', 'no_action']:
            errors.append(f"{case_id}: Invalid case_status {ass.get('case_status')}")
        if not (0.0 <= ass.get('confidence', -1) <= 1.0):
            errors.append(f"{case_id}: Confidence out of range {ass.get('confidence')}")
        
        # 2. Affected entities limits
        ae = d.get('affected_entities', {})
        for field in ['order_ids', 'item_ids', 'seller_ids', 'payment_ids']:
            if len(ae.get(field, [])) > 5:
                errors.append(f"{case_id}: {field} exceeds limit of 5")

        # 3. Evidence IDs
        evs = d.get('evidence_ids', [])
        if len(evs) > 10:
            errors.append(f"{case_id}: evidence_ids exceeds limit of 10")
        for ev in evs:
            if not evidence_pattern.match(ev):
                errors.append(f"{case_id}: Invalid evidence ID format: {ev}")

        # 4. Root cause analysis
        rca = d.get('root_cause_analysis', {})
        if len(rca.get('ranked_causes', [])) > 3:
            errors.append(f"{case_id}: ranked_causes exceeds limit of 3")
        if len(rca.get('responsible_parties', [])) > 3:
            errors.append(f"{case_id}: responsible_parties exceeds limit of 3")

        # 5. Resolution actions
        if len(d.get('resolution_actions', [])) > 5:
            errors.append(f"{case_id}: resolution_actions exceeds limit of 5")

    if errors:
        print("VERIFICATION FAILED:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("ALL 50 CASES PASSED VERIFICATION PERFECTLY!")

if __name__ == "__main__":
    verify()
