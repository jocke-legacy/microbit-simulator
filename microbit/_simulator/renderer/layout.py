import enum
from typing import List, Dict, Union


class Direction(enum.Enum):
    HORIZONTAL = 'x'
    VERTICAL = 'y'


class Layoutable:
    __slots__ = (
        'x',
        'y',
        'width',
        'height',
        'flex',
        'start',
        'size'
    )

    def __init__(self, start=None, size=None, flex=True):
        self.x = self.y = self.height = self.width = None

        self.start = start
        self.size = size
        self.flex = flex

    def _pop_request_kwargs(self, kwargs):
        return {key: kwargs.pop(key, None)
                for key in Layoutable.__slots__}

    def request(self, **kwargs):
        for key, value in kwargs.items():
            if key not in Layoutable.__slots__:
                raise ValueError('Invaild argument {!r}={!r}'.format(key, value))
            setattr(self, key, value)


class Area:
    __slots__ = ('x', 'y')

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __add__(self, other: 'Area'):
        if not isinstance(other, Area):
            raise NotADirectoryError

        return Area(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Area'):
        if not isinstance(other, Area):
            raise NotADirectoryError

        return Area(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise NotADirectoryError
        return Area(self.x * other, self.y * other)

    def __neg__(self):
        return Area(-self.x, -self.y)


class Box(Layoutable):
    __slots__ = Layoutable.__slots__ + (
        'name',
    )

    def __init__(self, name=None, **kwargs):
        self.name = name
        super(Box, self).__init__(**kwargs)

    @property
    def area(self) -> Area:
        return Area(self.width, self.height)


class Layout(Layoutable):
    __slots__ = (
        'elements',
        'direction',
    )

    def __init__(self, direction: Direction,
                 *elements: List[Layoutable],
                 **kwargs):
        self.direction = direction
        self.elements = elements
        super(Layout, self).__init__(**kwargs)


class LinearBudget:
    __slots__ = (
        'initial',
        'transactions',
    )

    def __init__(self, initial):
        self.initial = initial

    @property
    def available(self):
        return self.initial - sum(self.transactions)


def solve(layout: Layout):
    initial = layout.height if layout.direction == Direction.VERTICAL else \
        layout.width
    budget = LinearBudget(initial)

    fixed_elements = [element for element in layout.elements
                      if element.flex is False]

    if sum([element.size ])

    for element in layout.elements:
        budget.
        element.size


class Budget:
    __slots__ = (
        'area',
        'transactions',
    )

    def __init__(self, x: int, y: int):
        self.area = Area(x, y)
        self.transactions = [Area(0, 0)]

    @property
    def x(self):
        return self.area.x

    @x.setter
    def x(self, value):
        self.area.x = value

    @property
    def y(self):
        return self.area.y

    @y.setter
    def y(self, value):
        self.area.y = value

    @property
    def allocated(self):
        return sum(self.transactions, Area(0, 0))

    @property
    def available(self):
        return self.area - self.allocated

    def deduct(self, area: Area):
        self.transactions.append(-area)
