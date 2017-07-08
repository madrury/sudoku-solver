

class Board:

    def __init__(self):
        self.board = {
            (i, j): None for i in range(9) for j in range(9)
        }
        self.level = None
        self.id = None

    @classmethod
    def read_from_json(cls, jsn):
        board = cls()
        data = json.loads(jsn)
        for ij, (mask_bit, num) in enumerate(zip(data['mask'], data['puzzle'])):
            i, j = ij // 9, ij % 9
            if mask_bit = '1':
                self.board[(i, j)] = int(num)
        self.level = int(data['level'])
        self.id = data['id']
