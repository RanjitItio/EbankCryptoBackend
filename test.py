from block_io import BlockIo


dogecoin = BlockIo('09d7-7b5c-a11d-a233','AEB8E42FA8E59592')
litcoin = BlockIo('ee6a-5cb6-4f85-3247','AEB8E42FA8E59592')
bitcoin = BlockIo('0d25-0de7-1052-e04a','AEB8E42FA8E59592')
address="2MscM7HNHeedb42DVgn8b98zeynUAD6EsZv"

transactions = dogecoin.prepare_transaction(amounts='5',from_addresses='2N5kLFSD5EJPtegdnfYFFN7BTouAbLRL3km',to_addresses=address ,priority='high')
