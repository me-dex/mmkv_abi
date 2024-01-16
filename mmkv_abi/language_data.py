class LanguageData:
    @staticmethod
    def find_utf16_terminator(data):
        for i in range(0, len(data), 2):
            if data[i:i + 2] == b'\x00\x00':
                return i
            
        return None

    def __init__(self, unpacked_data):
        self._table = {}

        data_view = memoryview(unpacked_data)
        count = int.from_bytes(data_view[0:4], 'little')

        for i in range(4, 4 * (count + 1), 4):
            _id = int.from_bytes(data_view[i:i + 4], 'little')
            offset = int.from_bytes(data_view[i + (count * 4):i + (count * 4) + 4], 'little')

            start = offset * 4
            end = start + self.find_utf16_terminator(data_view[start:])
            value = str(data_view[start:end], 'utf-16')

            self._table[_id] = value

    def __getitem__(self, index):
        return self._table[index]
