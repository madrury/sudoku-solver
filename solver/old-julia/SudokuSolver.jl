module SudokuSolver

  import Base.show
  export House, Row, Column, Square, 
         houseof,
         MarkedBoard, 
         iter, 
         mark!,
         markup,
         test_board_1

  # Temporary
  typealias Move Integer

  # Board:
  #   Represents a sudoku board in some state of play.
  # 
  # Fields:
  #   - entries: 
  #       The current entries in the board.  A matrix holding integers
  #     1-9, with the additional value -1 signifying that a value in the 
  #     board is unknown.
  #   - mask: 
  #       A boolean matrix masking the values unknown in the initial
  #     puzzle.
  type Board
    entries::Matrix{Int64}
    mask::Matrix{Bool}

    # Construct a board from two 81-entry arrays.
    function Board(entries::Vector{Int}, mask::Vector{Bool})
      @assert size(entries) == (81,)
      @assert size(mask) == (81,)
      board = new()
      board.entries = reshape(entries, 9, 9)
      board.mask = reshape(mask, 9, 9)
      board
    end
    # Construct a board from two matricies.
    function Board(entries::Matrix{Int}, mask::Vector{Bool})
      @assert size(entries) == (9,9)
      @assert size(mask) == (9,9)
      new(entries, mask)
    end
  end

  # MarkedBoard Type:
  #   Holds marks for each cell in a puzzle indication what symbols can-not
  # go there.
  type MarkedBoard 
    marks::Matrix{Set{Integer}}
    foundmoves::Vector{Move}
  end
  MarkedBoard(marks::Matrix{Set{Integer}}) = MarkedBoard(marks, Vector{Move}[])
  MarkedBoard() = MarkedBoard(reshape([Set{Integer}() for i in 1:81], 9, 9))
  
  include("Houses.jl")
  include("Board.jl")
  include("MarkedBoard.jl")

  test_board_1 = Board(
    [parseint(ch) for ch in 
    "691547832285361794437829651542918376819673425376452189928136547764285913153794268"],
    [parseint(ch) == 1 for ch in 
      "101010011010010011011111100011011011101010101110110110001111110110010010110010101"]
  )

end
