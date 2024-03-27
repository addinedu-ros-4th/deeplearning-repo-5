class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        
    def get_words_with_prefix(self, prefix):
        if not prefix:  # 만약 접두사가 공백이면 빈 리스트를 반환
            return []

        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        self._collect_words(node, prefix, words)
        return words
    
    def _collect_words(self, node, prefix, words):
        if node.is_end_of_word:
            words.append(prefix)
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, words)