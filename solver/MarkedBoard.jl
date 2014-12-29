export MarkedBoard, iter, mark!

# Temporary
typealias Move Integer

# MarkedBoard Type:
#   Holds marks for each cell in a puzzle indication what symbols can-not
# go there.
type MarkedBoard 
  marks::Matrix{Set{Integer}}
  foundmoves::Vector{Move}
end
MarkedBoard(marks::Matrix{Set{Integer}}) = MarkedBoard(marks, Vector{Move}[])
MarkedBoard() = MarkedBoard(reshape([Set{Integer}() for i in 1:81], 9, 9))

function getindex(board::MarkedBoard, ix::Integer, jx::Integer)
  board.marks[ix, jx]
end


# Multimethod for iterating over all the marksets in a given house.
function iter(board::MarkedBoard, row::Row)
  function iterrow()
    for jx in 1:9
      produce(board[row.ix, jx])
    end
  end
  Task(iterrow)
end

function iter(board::MarkedBoard, col::Column)
  function itercol()
    for ix in 1:9
      produce(board[ix, col.jx])
    end
  end
  Task(itercol)
end

function iter(board::MarkedBoard, squ::Square)
  function itersqu()
    for k1 in 0:2, k2 in 0:2
      produce(board[3*squ.kx[1] - 2 + k1, 3*squ.kx[2] - 2 + k2])
    end
  end
  Task(itersqu)
end

# Mark every cell in a house with a given symbol.
function mark!(board::MarkedBoard, house::House, sym::Integer)
  for markedcell in iter(board, house)
    push!(markedcell, sym)
  end
end
