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

    try:
        # Handle constraints
        if isinstance(obj, cp.constraints.constraint.Constraint):
            print(f"  Constraint: {obj}")
            print(f"  Left hand side:")
            print_cvxpy_object(obj.args[0])
            print(f"  Right hand side:")
            print_cvxpy_object(obj.args[1])
            return

        # Handle comparison operators
        if isinstance(obj, (cp.atoms.affine.binary_operators.AddExpression,
                           cp.atoms.affine.binary_operators.MulExpression)):
            print(f"  Expression: {obj}")
            print(f"  Left operand:")
            print_cvxpy_object(obj.args[0])
            print(f"  Right operand:")
            print_cvxpy_object(obj.args[1])
            return

        # Handle Sum
        if isinstance(obj, cp.atoms.affine.sum.Sum):
            print(f"  Sum: {obj}")
            print(f"  Expression:")
            print_cvxpy_object(obj.args[0])
            return

        # Handle Hstack and Vstack
        if isinstance(obj, (cp.atoms.affine.vstack.Vstack,
                          cp.atoms.affine.hstack.Hstack)):
            print(f"  {type(obj).__name__}: {obj}")
            print(f"  Shape: {obj.shape}")
            print(f"  Args:")
            for arg in obj.args:
                print_cvxpy_object(arg)
            return

        # Handle Promote
        if isinstance(obj, cp.atoms.affine.promote.Promote):
            print(f"  Promote: {obj}")
            print(f"  Shape: {obj.shape}")
            print(f"  Value: {obj.value}")
            print(f"  Expression:")
            print_cvxpy_object(obj.args[0])
            return

        # Handle reshape
        if isinstance(obj, cp.atoms.affine.reshape.reshape):
            print(f"  Reshape: {obj}")
            print(f"  Shape: {obj.shape}")
            print(f"  Expression:")
            print_cvxpy_object(obj.args[0])
            return

        # Handle variables
        if isinstance(obj, cp.Variable):
            print(f"  Variable: {obj.name()}")
            print(f"  Shape: {obj.shape}")
            print(f"  Value: {obj.value}")
            if (obj.shape): # not empty
                for i in range(obj.shape[0]):
                    print_cvxpy_object(obj[i])
            return

        # Handle index
        if isinstance(obj, cp.atoms.affine.index.index):
            print(f"  Index: {obj}")
            print(f"  Name: {obj.name()}")
            print(f"  Shape: {obj.shape}")
            print(f"  Value: {obj.value}")
            return

        # Handle binary operators (==, <=, >=)
        if hasattr(obj, 'args') and len(obj.args) == 2:
            print(f"  Binary operator: {obj}")
            print(f"  Left operand:")
            print_cvxpy_object(obj.args[0])
            print(f"  Right operand:")
            print_cvxpy_object(obj.args[1])
            return

        # Default case
        print(f"  Unknown object type: {type(obj)}")
        print(f"  String representation: {obj}")
        if hasattr(obj, 'args'):
            print(f"  Args: {obj.args}")

    except Exception as e:
        print(f"  Error processing object: {str(e)}")
        print(f"  String representation: {obj}")