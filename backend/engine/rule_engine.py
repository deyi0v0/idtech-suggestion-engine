from dataclasses import dataclass
from typing import List, Callable
from pydantic import BaseModel

# Data Models
#-------------------

#fields subject to change
@dataclass(frozen=True)
class Hardware: 
    id: int
    model: str
    device_type: str
    connection_types: List[str]
    emv: bool
    contactless: bool

#fields subject to change
@dataclass(frozen=True)
class Software:
    id: int
    name: str
    platform: str

@dataclass(frozen=True)
class Device:
    hardware: Hardware
    software: Software

#Placeholders
class Requirements(BaseModel):
    needs_contactless: bool = False
    needs_pin: bool = False
    needs_emv: bool = False


class EnvironmentInfo(BaseModel):
    platform: str
    connection_types: List[str]


class RecommendRequest(BaseModel):
    environment: EnvironmentInfo
    requirements: Requirements


class RuleResult(BaseModel):
    rule: str
    passed: bool
    message: str


#Defining Rules
#------------------

RuleFn = Callable[[RecommendRequest, Device], RuleResult]  

@dataclass(frozen=True)
class RuleSpec:
    id: str             #unique identifier for the rule
    name: str           #human-readable name for the rule
    description: str = ""
    required: bool = True
    #weight: int = 1

@dataclass(frozen=True)
class Rule:
    specs: RuleSpec
    fn: RuleFn    

    
RULES: List[Rule] = []      #list of rules to eval


#------------
# evaluation section

class DeviceEvaluation(BaseModel):
    device_id: int
    passed_required: bool
    score: int
    results: List[RuleResult]
    failed_required_rule_ids: List[str] = []


class Recommendation(BaseModel):
    device_id: int
    score: int
    evaluation: DeviceEvaluation


#req is the merchants needs, hardware is the hardware from the device that is being evaluated
def evaluate_compatability(req: RecommendRequest, device: Device) -> DeviceEvaluation:
    results: List[RuleResult] = []
    score = 0   
    failed_rules_id: List[str] = []

    for rule in RULES:
        result = rule.fn(req, device)
        results.append(result)

        if result.passed:
            score += 1

        else:
            if rule.specs.required:
                failed_rules_id.append(rule.specs.id) 

    return DeviceEvaluation(
        device_id=device.hardware.id,
        passed_required=len(failed_rules_id) == 0,
        score=score,
        results=results,
        failed_required_rule_ids=failed_rules_id
    )


#maybe add how many to return -- might be a hard cap or maybe not
def recommend(req: RecommendRequest, devices: List[Device]) -> List[Recommendation]:
    evaluations: List[DeviceEvaluation] = [
        evaluate_compatability(req, device) for device in devices
    ]

    compatible = [e for e in evaluations if e.passed_required]
    compatible.sort(key=lambda e: e.score, reverse=True)

    return [
        Recommendation(device_id=e.device_id, score=e.score, evaluation=e)
        for e in compatible
    ]


#Rule functions
#--------------------
#Examples/Placeholders (These are not real rules yet)

def connection_match(req: RecommendRequest, device: Device) -> RuleResult:
    if any(conn in device.hardware.connection_types for conn in req.environment.connection_types):
        return RuleResult(rule="Connection Match", passed=True, message="Hardware connection types match environment.")
    else:
        return RuleResult(rule="Connection Match", passed=False, message="No matching connection types between hardware and environment.")
