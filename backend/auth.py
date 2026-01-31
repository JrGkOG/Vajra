class AccessControl:
    """
    Manages Role-Based Access Control (RBAC) using a simplified Bell-LaPadula model.
    Clearance Levels: Lower number = Higher Privilege.
    """
    
    # Clearance Constants
    CLEARANCE_TOP_SECRET = 1 # Director
    CLEARANCE_SECRET = 2
    CLEARANCE_CONFIDENTIAL = 3 # Operator
    
    # Role Mapping
    ROLES = {
        "DIRECTOR": CLEARANCE_TOP_SECRET,
        "OPERATOR": CLEARANCE_CONFIDENTIAL,
        "SATELLITE": CLEARANCE_TOP_SECRET # System level
    }

    @staticmethod
    def get_clearance(role: str) -> int:
        return AccessControl.ROLES.get(role.upper(), 99) # 99 = No Access

    @staticmethod
    def can_read(user_role: str, file_classification: int) -> bool:
        """
        No Read Up: User can read if User Clearance <= File Classification.
        Example: 
            Director (1) <= Low_File (3) -> True.
            Operator (3) <= High_File (1) -> False.
        """
        user_level = AccessControl.get_clearance(user_role)
        return user_level <= file_classification

    @staticmethod
    def can_write(user_role: str, target_classification: int) -> bool:
        """
        No Write Down: User can write if User Clearance >= Target Classification.
        (Prevents leaking high secrets to low channels)
        """
        user_level = AccessControl.get_clearance(user_role)
        return user_level >= target_classification
