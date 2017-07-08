
# Display a sudoku board, ascii style.
function Base.show(io::IO, board::Board)
  hsep = repeat("-", 13)
  for i = 1:9
    if i%3 == 1
      println(hsep)
    end
    for j in 1:9
      if j%3 == 1
        print("|")
      end
      if board.mask[i, j]
        print(board.entries[i, j])
      else
        print(" ")
      end
      if j == 9
        print("|\n")
      end
    end
  end
  println(hsep)
end

# Lookup an entry in a board.
function getindex(board::Board, ix::Int, jx::Int)
  @assert (1 <= ix <= 3)
  @assert (1 <= jx <= 3)
  board.entries[ix, jx]
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

