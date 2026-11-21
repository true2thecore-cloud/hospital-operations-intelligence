"""Interactive local onboarding. Saves configuration/prompts, never grants connector access."""
import argparse
import json
import re
from pathlib import Path
from .readiness import read, validate_profile


def ask(label, default):
    answer = input(f'{label} [{default}]: ').strip()
    return answer or str(default)


def generate(p, out):
    validate_profile(p)
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty output folder to avoid overwriting local setup.')
    out.mkdir(parents=True, exist_ok=True)
    (out/'profile.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
    fields = {f['key']:f for f in p['fields']}
    for m in p['meetings']:
        text = '# Extraction for '+m['label']+'\n\n'+m['focus']+'\n\n'
        text += 'Use prompts/meeting-extraction.md and the version-2 reviewed-meeting contract. This is a draft until a reviewer confirms the evidence.\n\n'
        text += '| Field | Meaning | Type / unit |\n| --- | --- | --- |\n'
        for k in m['fields']:
            f=fields[k];text+=f"| {k} | {f['definition']} | {f['type']} / {f.get('unit','')} |\n"
        text+='\nPreserve source locators, observedAt and appliesToDate. Do not infer values, severity or owners.\n'
        (out/(m['key']+'-extraction.md')).write_text(text,encoding='utf-8')
    (out/'SETUP-REVIEW.md').write_text('# Review before connecting\n\nConfirm meeting identities, field definitions, source scope, date rules and workbook destination. Connection access has not been granted or tested. Automation preferences do not install flows. Follow docs/AUTOMATION-SETUP.md after a manual synthetic test.\n',encoding='utf-8')


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--profile',default='config/readiness.example.json')
    a.add_argument('--out',default='data/setup')
    a.add_argument('--from-profile',action='store_true',help='Generate prompts from an already reviewed profile without questions')
    args=a.parse_args();p=read(args.profile)
    if not args.from_profile:
        print('This questionnaire creates local setup files. It does not access accounts or deploy agents.')
        p['siteLabel']=ask('Organization label',p['siteLabel'])
        p['siteKey']=ask('Stable organization key',p['siteKey'])
        if not re.fullmatch(r'[a-z][a-z0-9_]+',p['siteKey']): raise ValueError('Use a lowercase site key.')
        p['timezone']=ask('IANA timezone',p['timezone'])
        p['workbookName']=ask('Readiness workbook name',p['workbookName'])
        p['workbookLocation']=ask('Approved workbook storage location',p['workbookLocation'])
        p['closingTime']=ask('Local daily closing time, HH:MM',p['closingTime'])
        p['transcriptDelayMinutes']=int(ask('Minutes after meeting end to check transcripts',p['transcriptDelayMinutes']))
        chosen=[]
        for m in p['meetings']:
            if ask('Include '+m['label']+'? yes/no','yes').lower()!='yes': continue
            m['label']=ask('Local meeting name',m['label'])
            m['end']=ask('Scheduled end, HH:MM',m['end'])
            m['weekdays']=[int(x) for x in ask('Weekdays, Monday=0, comma-separated',','.join(map(str,m['weekdays']))).split(',')]
            m['focus']=ask('What must leaders know from this meeting?',m['focus'])
            m['calendarMatch']=ask('Exact approved calendar series identifier or name','Not configured')
            m['sourceRoute']=ask('Source route: manual_vtt, email, graph, shared_file',m['sourceRoute'])
            print('Available fields: '+', '.join(f['key'] for f in p['fields']))
            m['fields']=ask('Fields for this meeting, comma-separated',','.join(m['fields'])).replace(' ','').split(',')
            chosen.append(m)
        p['meetings']=chosen
        for source in p['sources']:
            source['enabled']=ask('Use approved '+source['kind']+' source? yes/no','no').lower()=='yes'
            if source['enabled']: source['location']=ask('Location or scope for '+source['kind'],'Not configured')
            source['accessVerified']=False
        for k in ('transcriptDelivery','workbookRefresh','confirmation','morningBrief','audio'):
            p['automation'][k]=ask('Request optional '+k+' setup? yes/no','no').lower()=='yes'
        if p['automation']['morningBrief']: p['automation']['briefTime']=ask('Morning brief local time',p['automation']['briefTime'])
    generate(p,args.out)
    print('Created local configuration and meeting prompts in '+args.out+'. Review these before tenant setup.')


if __name__=='__main__': main()
