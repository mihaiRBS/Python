#!../venv/bin/python3
"""
Summary: Fabrix Provision DC Workflow.

Author: Neil Baillie <neilbaillie@hutchinsonnetworks.com>.
"""

import sys
sys.path.append('../')
import traceback
import json

from workflows.utlis import workflow
from infrastructure.ucsd import UCSD
from infrastructure.apic import APIC
from infrastructure.ucsm import UCSM
from infrastructure.f5 import F5
from infrastructure.vmware import VCNT

from infrastructure_config import UCSD_ADDR
from infrastructure_config import UCSD_API_KEY
from infrastructure_config import APIC_ADDR
from infrastructure_config import APIC_USERNAME
from infrastructure_config import APIC_PASSWORD
from infrastructure_config import UCSM_ADDR
from infrastructure_config import UCSM_USERNAME
from infrastructure_config import UCSM_PASSWORD
from infrastructure_config import F5_ADDR
from infrastructure_config import F5_USERNAME
from infrastructure_config import F5_PASSWORD
from infrastructure_config import VCNT_ADDR
from infrastructure_config import VCNT_USERNAME
from infrastructure_config import VCNT_PASSWORD

class StopWorkflow(Exception):
    """Stop Worflow."""

    def __init__(self, wf, kwargs):
        wf.status = "Halted"

def run():
    """Run the Needed Workflow Elements."""
    ucsdaddr = UCSD_ADDR['LND'][0]
    ucsdapikey = UCSD_API_KEY['LND'][0]
    apicaddrs = APIC_ADDR
    apicusernames = APIC_USERNAME
    apicpasswords = APIC_PASSWORD
    ucsmaddrs = UCSM_ADDR
    ucsmusernames = UCSM_USERNAME
    ucsmpasswords = UCSM_PASSWORD
    f5addrs = F5_ADDR
    f5usernames = F5_USERNAME
    f5passwords = F5_PASSWORD
    vcntaddrs = VCNT_ADDR
    vcntusernames = VCNT_USERNAME
    vcntpasswords = VCNT_PASSWORD

    wf = workflow.Workflow()
    try:
        # Load Infrastructure Classes Here
        ucsd = UCSD(ucsdaddr, ucsdapikey)

        apics = {}
        for dc, addrs in apicaddrs.items():
            for apic_addr in addrs:
                apics[apic_addr] = APIC(apic_addr, apicusernames[dc], apicpasswords[dc])

        ucsms = {}
        for dc, addrs in ucsmaddrs.items():
            for ucsm_addr in addrs:
                ucsms[ucsm_addr] = UCSM(ucsm_addr, ucsmusernames[dc], ucsmpasswords[dc])

        f5s = {}
        for dc, addrs in f5addrs.items():
            for f5_addr in addrs:
                f5s[f5_addr] = F5(f5_addr, f5usernames[dc], f5passwords[dc])

        vcnts = {}
        for dc, addrs in vcntaddrs.items():
            for vcnt_addr in addrs:
                vcnts[vcnt_addr] = VCNT(vcnt_addr, vcntusernames[dc], vcntpasswords[dc])

        # Start Of Tasks #####################################################

        wf.task("UcsdVer", ucsd.get_version, {})
        if len(wf.data["UcsdVer"]) <= 4:
            raise StopWorkflow(wf, {"Condition": "Ver Check Failed"})

        for apic_addr, apic in apics.items():
            wf.task("ApicVer-" + apic_addr, apic.get_version, {})
            if len(wf.data["ApicVer-" + apic_addr]) < 4:
                pass
                # Fix later API not returning "version" might need to have a target version in GUI.
                #raise StopWorkflow(wf, {"Condition": "Ver Check Failed"})

        for ucsm_addr, ucsm in ucsms.items():
            wf.task("UCSMVer-" + ucsm_addr, ucsm.get_version, {})
            if len(wf.data["UCSMVer-" + ucsm_addr]) < 4:
                raise StopWorkflow(wf, {"Condition": "Ver Check Failed"})

        for f5_addr, f5 in f5s.items():
            wf.task("F5Ver-" + f5_addr, f5.get_version, {})
            if len(wf.data["F5Ver-" + f5_addr]) < 4:
                raise StopWorkflow(wf, {"Condition": "Ver Check Failed"})

        for vcnt_addr, vcnt in vcnts.items():
            wf.task("vCenterVer-" + vcnt_addr, vcnt.get_version, {})
            if len(wf.data["vCenterVer-" + vcnt_addr]) < 4:
                raise StopWorkflow(wf, {"Condition": "Ver Check Failed"})

        # End Of Tasks #######################################################
        wf.currenttaskname = ""
        wf.status = "Complete"

    except StopWorkflow as e:
        wf.logger.info(e.args[1]["Condition"])

    except:
        wf.logger.debug(sys.exc_info()[0])
        wf.logger.debug(traceback.print_exc())
        wf.status = "Failed"
    finally:
        return(wf.output())


if __name__ == '__main__':
    from argparse import ArgumentParser

    argsp = ArgumentParser()

    args = argsp.parse_args()

    result = run()
    print(json.dumps(json.loads(result), sort_keys=True, indent=4, separators=(',', ': ')))
