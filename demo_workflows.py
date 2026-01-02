"""
Demo workflows for testing lazyverdi
This script creates various AiiDA calculations and workflows to populate the database
"""

from aiida import orm, engine, load_profile
from aiida.engine import submit, run, run_get_node, calcfunction, WorkChain, ToContext
import time

# Load AiiDA profile
load_profile()


@calcfunction
def add(x, y):
    """Add two integers"""
    return orm.Int(x.value + y.value)


@calcfunction
def multiply(x, y):
    """Multiply two integers"""
    return orm.Int(x.value * y.value)


@calcfunction
def power(x, y):
    """Power of two integers"""
    return orm.Int(x.value**y.value)


class MultiplyAddWorkChain(WorkChain):
    """Simple workflow: (x * y) + z"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input("x", valid_type=orm.Int)
        spec.input("y", valid_type=orm.Int)
        spec.input("z", valid_type=orm.Int)
        spec.output("result", valid_type=orm.Int)
        spec.outline(
            cls.multiply_step,
            cls.add_step,
        )

    def multiply_step(self):
        """Multiply x and y"""
        result = multiply(self.inputs.x, self.inputs.y)
        self.ctx.product = result

    def add_step(self):
        """Add product and z"""
        result = add(self.ctx.product, self.inputs.z)
        self.out("result", result)


def create_simple_calculations():
    """Create simple Int calculations without requiring codes"""
    nodes = []

    # Create several calculations
    for i in range(3):
        x = orm.Int(i + 1)
        y = orm.Int(2)

        result, node = run_get_node(add, x=x, y=y)
        nodes.append(node)
        print(f"Created add calculation: {node.pk} -> {result.value}")

        result, node = run_get_node(multiply, x=x, y=y)
        nodes.append(node)
        print(f"Created multiply calculation: {node.pk} -> {result.value}")

        if i < 2:  # Keep power small
            result, node = run_get_node(power, x=x, y=y)
            nodes.append(node)
            print(f"Created power calculation: {node.pk} -> {result.value}")

    return nodes


def create_workflow_demo():
    """Create a simple workflow using workchain"""
    nodes = []

    # Submit several workflows
    for i in range(3):
        try:
            builder = MultiplyAddWorkChain.get_builder()
            builder.x = orm.Int(i + 1)
            builder.y = orm.Int(3)
            builder.z = orm.Int(10)

            node = submit(builder)
            nodes.append(node)
            print(f"Submitted MultiplyAddWorkChain: {node.pk}")
        except Exception as e:
            print(f"Could not submit workflow: {e}")

    return nodes


def create_data_nodes():
    """Create various data nodes"""
    nodes = []

    # Create Int nodes
    for i in range(5):
        node = orm.Int(i * 10)
        node.store()
        nodes.append(node)
        print(f"Created Int node: {node.pk} = {node.value}")

    # Create Float nodes
    for i in range(5):
        node = orm.Float(i * 3.14)
        node.store()
        nodes.append(node)
        print(f"Created Float node: {node.pk} = {node.value}")

    # Create Str nodes with labels
    labels = ["input_file", "output_file", "config", "parameters", "metadata"]
    for label in labels:
        node = orm.Str(f"content_of_{label}")
        node.label = label
        node.description = f"Demo string node: {label}"
        node.store()
        nodes.append(node)
        print(f"Created Str node: {node.pk} ({label})")

    # Create Dict nodes
    for i in range(3):
        node = orm.Dict(
            {
                "iteration": i,
                "parameters": {
                    "cutoff": 30 + i * 10,
                    "kpoints": [4, 4, 4],
                    "pseudo_family": "SSSP/1.3/PBEsol/efficiency",
                },
                "settings": {"cmdline": ["-nk", "4"]},
            }
        )
        node.label = f"config_{i}"
        node.store()
        nodes.append(node)
        print(f"Created Dict node: {node.pk} (config_{i})")

    # Create List nodes
    for i in range(2):
        node = orm.List([1, 2, 3, 4, 5 + i])
        node.label = f"list_{i}"
        node.store()
        nodes.append(node)
        print(f"Created List node: {node.pk}")

    return nodes


def main():
    """Run all demo creation functions"""
    print("=" * 60)
    print("Creating AiiDA demo data for lazyverdi testing")
    print("=" * 60)

    print("\n[1/3] Creating data nodes...")
    data_nodes = create_data_nodes()
    print(f"Created {len(data_nodes)} data nodes")

    print("\n[2/3] Creating simple calculations...")
    calc_nodes = create_simple_calculations()
    print(f"Created {len(calc_nodes)} calculation nodes")

    print("\n[3/3] Creating workflows...")
    wf_nodes = create_workflow_demo()
    print(f"Submitted {len(wf_nodes)} workflow nodes")

    print("\n" + "=" * 60)
    print("Demo creation complete!")
    print("=" * 60)
    print(f"\nTotal nodes created/submitted: {len(data_nodes) + len(calc_nodes) + len(wf_nodes)}")
    print("\nYou can now use lazyverdi to explore these nodes:")
    print("  python -m lazyverdi.app")
    print("\nOr check with verdi:")
    print("  verdi process list")
    print("  verdi process list -a")
    print("  verdi data core.int list")


if __name__ == "__main__":
    main()
