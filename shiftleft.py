import requests
import json
import os
metadata = dict()
metadata['template_local_store_name'] = 'template.json'
metadata['shn_url'] = 'https://shnreg.myshn.net/labs/rest/api/awscf/scan/stacktemplate'


class ConfigAuditFailed(Exception):
    print("Violated config audit policies ")
    pass


def validator(template):
    print("Sending data to SHN CASBOps")

    with open(template, 'r') as read_file_data:
        cf_data1 = json.load(read_file_data)
    # print(cf_data1)
    with open(metadata['template_local_store_name'], 'w') as outfile:
        json.dump(cf_data1, outfile)
    multipart_form_data = {'file': (
        'template.zip',
        open(os.path.abspath(
            metadata['template_local_store_name']
        ), 'rb')
    ), }
    userName = get_variable('BITBUCKET_REPO_OWNER', required=True)
    values = {
        'stackName': template,
        'userName': userName,
        'email': 'NA',
        'regionName': 'NA',
        'accountId': 'NA'
    }
    print("Posting template to: " + metadata['shn_url'])
    response = requests.post(
        metadata['shn_url'],
        data=values,
        files=multipart_form_data
    )
    print("Response Code from SHN is: " + str(response.status_code))
    response_message = json.loads(response.text)
    template_compliance = json.dumps(
        eval(response_message['message']),
        indent=2
    )
    template_compliance_data = json.loads(str(template_compliance)[1:-1])
    if template_compliance_data['file_results']['violations']:
        print("Following violations are detected:")
        high_severity = None
        for i in template_compliance_data['file_results']['violations']:
            print("{}: {}".format(i['type'], i['message']))
            if i['type'] != 'WARN':
                high_severity = True
        if high_severity:
            print("Terminating further actions, since the template has high severity violations")
        raise Exception("Config Audit validation failed")
    else:
        print("Template has ZERO violations.")


def get_variable(name, required=False, default=None):
    value = os.getenv(name)
    if required and (value == None or not value.strip()):
        raise Exception('{} variable missing.'.format(name))
    return value if value else default


def main():
    diff = open("repository_diff.txt", "r")
    for file in diff:
        if file.rstrip().endswith(".json"):
            validator(file.rstrip())

    diff.close()


main()
