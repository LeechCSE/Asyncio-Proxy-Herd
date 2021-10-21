import config
import asyncio
import sys

async def tcp_client(server_id, message):
    reader, writer = await asyncio.open_connection(
        config.LOCALHOST, config.PORTS[server_id])
    
    print(f'Sending ... {message}')
    writer.write(message.encode())
    
    data = await reader.read(100)
    print(f'Received: {data.decode()}')
    
    print('Close connection')
    writer.close()
    
    
def main():
    server_id = sys.argv[1]
    args = sys.argv[2:]
    message = " ".join(args)
    
    asyncio.run(tcp_client(server_id, message))
    
if __name__ == '__main__':
    main()