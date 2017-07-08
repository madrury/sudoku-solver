# House Types:
#   The three subdivisions of the board are Row, Column, and Square, which
# are collectively called House(s).
abstract House

immutable Row <: House
  ix::Integer
  # Row indicies much be in 1:9.
  function Row(ix)
    @assert 1 <= ix <= 9
    new(ix)
  end
end
Row(ix, jx) = Row(ix)

immutable Column <: House
  jx::Integer
  # Column indicies must be in 1:9.
  function Column(jx)
    @assert 1 <= jx <= 9
    new(jx)
  end
end
Column(ix, jx) = Column(jx)

immutable Square <: House
  kx::(Integer, Integer)
  # Square index tuple must be in (1:3, 1:3).
  function Square(kx)
    @assert 1 <= kx[1] <= 3
    @assert 1 <= kx[2] <= 3
    new(kx)
  end
end
Square(ix, jx) = Square((ix, jx))

# Return the house of a given type occupied by a cell in the puzzle.
function houseof(ix::Integer, jx::Integer, T::DataType)
  @assert T <: House
  T(ix, jx)
end
