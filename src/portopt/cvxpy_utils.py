import cvxpy as cp

def print_object_info(obj, show="both", include_special=False):
    """
    Prints the attributes and methods of an object.
    
    Parameters:
        obj (object): The object to inspect.
        show (str, optional): Options: 'attributes', 'methods', or 'both' (default).
        include_special (bool, optional): Whether to include special members 
                                          (those starting with "_", "__", or being dunder methods). 
                                          Default is False.
    """
    attributes = []
    methods = []

    print(f"Object type: {type(obj)}")

    for name in dir(obj):
        if not include_special and name.startswith("_"):
            continue  # Skip special members unless explicitly requested
        
        try:
            attr = getattr(obj, name)
            attr_type = type(attr).__name__  # Get the type of the attribute
            
            if callable(attr):
                # Check if the method takes no arguments (except self)
                import inspect
                sig = inspect.signature(attr)
                if len(sig.parameters) == 1 and 'self' in sig.parameters:
                    try:
                        result = attr()
                        methods.append(f"{name}() : {attr_type} = {result}")
                    except Exception as e:
                        methods.append(f"{name}() : {attr_type} = <Error: {str(e)}>")
                else:
                    methods.append(f"{name}() : {attr_type}")
            else:
                attributes.append(f"{name} ({attr_type}) = {attr}")
        
        except Exception as e:
            attributes.append(f"{name} (Error) = <Error: {str(e)}>")

    if show in ("attributes", "both"):
        print("\nAttributes:")
        print("\n".join(attributes) if attributes else "  None")

    if show in ("methods", "both"):
        print("\nMethods:")
        print("\n".join(methods) if methods else "  None")

def print_cvxpy_object(obj):
    """
    Attempts to print out information about a cvxpy object.
    
    Only supports a subset of cvxpy objects and may not print out
    the information that is really needed.  To be extended over time
    as needed.
    """
    print(f"Type: {type(obj)}")
    if isinstance(obj, cp.Variable):
        print(f"  Name: {obj.name()} Shape: {obj.shape}")
        print(f"  Value: {obj.value}")
        if (obj.shape): # not empty
            for i in range(obj.shape[0]):
                print_cvxpy_object(obj[i])
    elif isinstance(obj, cp.atoms.affine.index.index):
        # This is an index into a variable array
        print(f"  Object: {obj}")
        print(f"  Name: {obj.name()} Shape: {obj.shape}")
        print(f"  Value: {obj.value}")
    elif isinstance(obj, cp.atoms.affine.vstack.Vstack) or \
         isinstance(obj, cp.atoms.affine.hstack.Hstack):
        print(f"  Name: {obj.name()} Shape: {obj.shape}")
        print(f"  Value: {obj.value}")
        print(f"  Args: {obj.args}")
        for arg in obj.args:
            print_cvxpy_object(arg)
    else:
        print(f"Unknown object type: {type(obj)}")
        print_object_info(obj)