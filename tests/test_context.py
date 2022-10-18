from glazy import GlazyContext, Resource
import dataclasses
import pytest
from copy import deepcopy, copy
from glazy.errors import XynResourceError


@GlazyContext
def test_decorator_on_direct_context_class(glazy_test_context):
    """ Test using GlazyContext class directly as a decorator (not a GlazyContext instance). """
    # This should be the GlazyContext that was created via `@GlazyContext`.
    assert GlazyContext.current() is not glazy_test_context

    # Since the `@GlazyContext` would have been created AFTER the standard unit-test `context`
    # fixture, the parent of my `@GlazyContext` would be the standard unit-test context fixture.
    assert GlazyContext.current().parent is glazy_test_context


@dataclasses.dataclass
class SomeResource(Resource):
    my_name: str = 'hello!'


module_level_context = GlazyContext.current()


def test_ensure_pytest_plugin_context_autouse_fixture_working():
    # Ensure by default every unit test that has glazy as a dependency will use
    # the context auto-use fixture; which makes a blank root-like context.
    assert GlazyContext.current() is not module_level_context

    # Ensure we have no items in the GlazyContext, that it is indeed blank.
    assert len(GlazyContext.current()._resources) == 0

    # Ensure app-root context also has no items in it, that it's blank.
    assert len(GlazyContext.current().parent._resources) == 0


# noinspection PyTypeChecker
# NOTE: This is not how you would normally do this, normally you would do:
#       >>> @SomeResource(my_name='first-name')
#       Doing it this way to test out giving initial resources to a new GlazyContext directly
#       instead of indirectly.
@GlazyContext(resources=[SomeResource(my_name='first-name')])
def test_decorator_on_context_object():
    first_resource = SomeResource.resource()
    assert first_resource.my_name == 'first-name'
    decorated_context = GlazyContext.current()

    new_resource = SomeResource(my_name='new-name')
    with GlazyContext(resources=[new_resource]) as with_context:
        assert with_context is not decorated_context, "Should be new context"
        # I created new GlazyContext and manually added new instance of SomeResource;
        # check to see if it's the current resource and looks intact.
        inside_resource = SomeResource.resource()
        assert inside_resource is not first_resource
        assert inside_resource is new_resource
        assert inside_resource.my_name == 'new-name'
        assert first_resource.my_name == 'first-name'

    with GlazyContext():
        assert with_context is not decorated_context, "Should be new context"
        # Check to see if when adding new GlazyContext, we still get the same SomeResource
        # instance, and that they still look intact with the correct values.
        assert SomeResource.resource() is first_resource
        assert first_resource.my_name == 'first-name'
        assert new_resource.my_name == 'new-name'


def test_context_and_with():
    root_context = GlazyContext.current()

    context_1 = GlazyContext(resources=[2])

    def verify_current_context_is_copy():
        copied_context = GlazyContext.current()
        # ensure they are not the same object (ie: it got copied), and the parent is correct.
        assert context_1 is not copied_context
        assert copied_context.parent is root_context

        # See if the non-active `context_1` can dynamically lookup it's parent as the
        # currently active GlazyContext.
        assert context_1.parent is copied_context

        # Ensure resources at copied.
        assert copied_context._resources == {int: 2}

    with context_1 as copied_context:
        # When we use GlazyContext via `@` or `with` or `make_current`, they should copy the
        # context and activate/make-current that copied context.
        assert GlazyContext.current() is copied_context
        verify_current_context_is_copy()

    # check to make sure same behavior happens when using context as a decorator.
    @context_1
    def my_method():
        verify_current_context_is_copy()

    my_method()


module_level_context = GlazyContext(
    resources=[
        20,
        "hello-str",
        SomeResource(my_name="start-name")
    ]
)


# I want to test it out here, because pycharm looks at the argument list of the function
# in order to know what (if any) fixtures to inject.
# If our decorator is not setup correctly, pytest won't call our test-method correctly.
# So having pycharm call our test method correctly is a really good edge-case test in of it's self!
@module_level_context
def test_module_level_context(glazy_test_context):
    # `context` is the base-context
    GlazyContext.current().add_resource(1.2)
    assert GlazyContext.current(for_type=float) == 1.2

    # Ensure that when we used the module-level-context, ensure it still uses the current
    # context as it's first parent. the `create=False` will ensure it won't add this looked
    # up resource to it's self.
    assert module_level_context.resource(for_type=float, create=False) == 1.2
    assert module_level_context is not GlazyContext.current()

    # Ensure that we have not float resource in the outer-module version (since create=False).
    assert float not in module_level_context._resources

    # See if the copied-context has the same resources still
    assert SomeResource.resource().my_name == "start-name"
    assert GlazyContext.current(for_type=int) == 20
    assert GlazyContext.current(for_type=str) == "hello-str"


def test_initial_context_resources_with_dict():
    my_context = GlazyContext(
        resources={int: 'string-as-int-resource', float: False, SomeResource: 'str-instead'}
    )

    with my_context:
        # SomeResource was replaced by a direct-string 'str-instead', testing replacing
        # resources with a completely different type (if you want to mock/test something specific).
        assert SomeResource.resource() == 'str-instead'
        assert GlazyContext.current(for_type=int) == 'string-as-int-resource'
        assert GlazyContext.current(for_type=float) is False


def test_deepcopy_context():
    c1 = GlazyContext()
    with pytest.raises(XynResourceError):
        deepcopy(c1)


@dataclasses.dataclass
class TestResource(Resource):
    my_name: str = 'hello!'


module_level_test_resource = TestResource.resource()
print(module_level_test_resource)
module_level_test_resource.my_name = "module-level-change"


# We run unit-test twice, ensure that each run of a unit test runs in it's own blank root context.
@pytest.mark.parametrize("test_run", [1, 2])
def test_module_level_resource_in_unit_test(test_run):
    # Make sure we have a different TestResource instance.
    assert module_level_test_resource is not TestResource.resource()

    # Check values, see if they are still at the module-level value
    assert TestResource.resource().my_name == "hello!"

    # Do a unit-test change, ensure we don't see it in another unit test.
    TestResource.resource().my_name = "unit-test-change"
    assert TestResource.resource().my_name == "unit-test-change"


def test_each_unit_test_starts_with_a_single_parentless_root_like_context():
    # Ensure we have no parent.
    unit_test_root_context = GlazyContext.current()

    # We should only have a thread-root context that is pointing to a single parent app-root.
    assert unit_test_root_context.parent.parent is None

    # Ensure we have no items in the GlazyContext, that it is indeed blank.
    assert len(unit_test_root_context._resources) == 0

    # Ensure app-root context also has no items in it, that it's blank
    assert len(unit_test_root_context.parent._resources) == 0

    # Ensure that when we use the root-like blank unit test context inside a `with` statement,
    # we have a new context with it's parent set at our root-like blank unit test context.
    with unit_test_root_context as new_context:
        assert unit_test_root_context is not new_context
        assert new_context.parent is unit_test_root_context


class TestSkipAttrOnCopyResource(Resource):
    attributes_to_skip_while_copying = ['my_attribute']
    my_attribute = "hello-1"  # Defined at class-level, not object-level
    my_other_attr = "hello-2"  # Defined at class-level, not object-level


def test_skip_attrs_on_resource_copy():
    r1 = TestSkipAttrOnCopyResource()
    assert r1.my_attribute == "hello-1"
    assert r1.my_other_attr == "hello-2"

    r1.my_attribute = 'changed_value-1'
    assert r1.my_attribute == "changed_value-1"

    r1.my_other_attr = 'changed_value-2'
    assert r1.my_other_attr == "changed_value-2"

    r2 = copy(r1)
    assert r2 is not r1

    assert r1.my_attribute == "changed_value-1"
    assert r1.my_other_attr == "changed_value-2"

    assert r2.my_attribute == "hello-1"
    assert r2.my_other_attr == "changed_value-2"

    r2.my_attribute = "changed_value-1.2"
    r2.my_other_attr = "changed_value-2.2"

    r3 = deepcopy(r2)
    assert r2.my_attribute == "changed_value-1.2"
    assert r2.my_other_attr == "changed_value-2.2"

    assert r3.my_attribute == "hello-1"
    assert r3.my_other_attr == "changed_value-2.2"
