from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import (
    CompatibilityMatrix, BloodType, RhType, BloodComponent,
    UrgencyLevel
)


class CompatibilityService:
    
    @staticmethod
    def is_compatible(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        component: BloodComponent,
        is_emergency: bool = False
    ) -> Tuple[bool, bool]:
        if component == BloodComponent.RBC:
            return CompatibilityService._rbc_compatible(
                donor_blood_type, donor_rh_type,
                recipient_blood_type, recipient_rh_type,
                is_emergency
            )
        elif component == BloodComponent.PLASMA:
            return CompatibilityService._plasma_compatible(
                donor_blood_type, donor_rh_type,
                recipient_blood_type, recipient_rh_type,
                is_emergency
            )
        elif component == BloodComponent.PLATELET:
            return CompatibilityService._platelet_compatible(
                donor_blood_type, donor_rh_type,
                recipient_blood_type, recipient_rh_type,
                is_emergency
            )
        elif component == BloodComponent.CRYOPRECIPITATE:
            return CompatibilityService._cryoprecipitate_compatible(
                donor_blood_type, donor_rh_type,
                recipient_blood_type, recipient_rh_type,
                is_emergency
            )
        return False, False

    @staticmethod
    def _rbc_compatible(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        is_emergency: bool
    ) -> Tuple[bool, bool]:
        is_emergency_use = False
        
        abo_ok = False
        if donor_blood_type == BloodType.O:
            abo_ok = True
            if recipient_blood_type != BloodType.O:
                is_emergency_use = True
        elif donor_blood_type == recipient_blood_type:
            abo_ok = True
        elif donor_blood_type == BloodType.A and recipient_blood_type == BloodType.AB:
            abo_ok = True
        elif donor_blood_type == BloodType.B and recipient_blood_type == BloodType.AB:
            abo_ok = True
        
        if not abo_ok:
            return False, False
        
        rh_ok = False
        if donor_rh_type == RhType.NEGATIVE:
            rh_ok = True
        elif donor_rh_type == recipient_rh_type:
            rh_ok = True
        
        if not rh_ok:
            if is_emergency and recipient_rh_type == RhType.POSITIVE:
                rh_ok = True
                is_emergency_use = True
            else:
                return False, False
        
        if is_emergency_use and not is_emergency:
            return False, False
        
        return True, is_emergency_use

    @staticmethod
    def _plasma_compatible(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        is_emergency: bool
    ) -> Tuple[bool, bool]:
        is_emergency_use = False
        
        abo_ok = False
        if donor_blood_type == BloodType.AB:
            abo_ok = True
        elif donor_blood_type == recipient_blood_type:
            abo_ok = True
        elif donor_blood_type == BloodType.A and recipient_blood_type == BloodType.AB:
            abo_ok = True
        elif donor_blood_type == BloodType.B and recipient_blood_type == BloodType.AB:
            abo_ok = True
        
        if not abo_ok:
            return False, False
        
        rh_ok = True
        
        return True, is_emergency_use

    @staticmethod
    def _platelet_compatible(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        is_emergency: bool
    ) -> Tuple[bool, bool]:
        is_emergency_use = False
        
        abo_ok = False
        if donor_blood_type == recipient_blood_type:
            abo_ok = True
        elif is_emergency:
            abo_ok = True
            is_emergency_use = True
        
        if not abo_ok:
            return False, False
        
        rh_ok = False
        if donor_rh_type == RhType.NEGATIVE:
            rh_ok = True
        elif donor_rh_type == recipient_rh_type:
            rh_ok = True
        elif is_emergency and recipient_rh_type == RhType.POSITIVE:
            rh_ok = True
            is_emergency_use = True
        
        if not rh_ok:
            return False, False
        
        return True, is_emergency_use

    @staticmethod
    def _cryoprecipitate_compatible(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        is_emergency: bool
    ) -> Tuple[bool, bool]:
        is_emergency_use = False
        
        abo_ok = False
        if donor_blood_type == BloodType.AB:
            abo_ok = True
        elif donor_blood_type == recipient_blood_type:
            abo_ok = True
        elif is_emergency:
            abo_ok = True
            is_emergency_use = True
        
        if not abo_ok:
            return False, False
        
        return True, is_emergency_use

    @staticmethod
    def get_compatible_blood_types(
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType,
        component: BloodComponent,
        is_emergency: bool = False
    ) -> List[Tuple[BloodType, RhType, bool]]:
        results = []
        for bt in BloodType:
            for rt in RhType:
                compatible, is_emergency_use = CompatibilityService.is_compatible(
                    bt, rt, recipient_blood_type, recipient_rh_type, component, is_emergency
                )
                if compatible:
                    results.append((bt, rt, is_emergency_use))
        return results

    @staticmethod
    def get_priority_score(
        donor_blood_type: BloodType,
        donor_rh_type: RhType,
        recipient_blood_type: BloodType,
        recipient_rh_type: RhType
    ) -> int:
        score = 0
        if donor_blood_type == recipient_blood_type:
            score += 100
        if donor_rh_type == recipient_rh_type:
            score += 50
        if donor_blood_type == BloodType.O:
            score -= 20
        if donor_rh_type == RhType.NEGATIVE:
            score -= 10
        return score
