#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>

#include <wiringPi.h>
#include <wiringPiSPI.h>

#define SS 8
#define DC 12

#define BUFFER_SIZE 12288
unsigned char pixel[BUFFER_SIZE];
unsigned char value;
int last_sequence[2] = {-1, -1};
bool flush = false;

void display()
{
    digitalWrite(DC, 1); 
    sleep(0.00000001);
    digitalWrite(DC, 0); 
    sleep(0.00000001);

    digitalWrite(SS, 0); 
    wiringPiSPIDataRW(0, pixel, BUFFER_SIZE);
    digitalWrite(SS, 1); 

    flush = false;
}

void update(char *data)
{
    char id[8];
    for (int i=0; i<8; i++) { id[i] = data[i]; }
    
    if (strcmp(id,"ArtNet"))
    {
        int opcode = data[8] + (data[9] << 8);
        int protocolVersion = (data[10] << 8) + data[11]; 
        if ((opcode==0x5000) && (protocolVersion >= 14))
        {
            int sequence = data[12];
            int universe = data[14] & 0x0F;
            int net = data[15];
            int data_length = (data[16] << 8) + data[17];
            
            memcpy(&pixel[512*(universe+net*16)], &data[18], data_length);

            if (last_sequence[net] != sequence)
            {
                if(net==1)
                {
                    display();
                }
            }
            last_sequence[net] = sequence;
        }
    }
}

int main(void)
{
    // GPIO
    wiringPiSetup();

    wiringPiSetupGpio();
    pinMode(SS, OUTPUT);
    pinMode(DC, OUTPUT);

    digitalWrite(SS, 1);
    digitalWrite(DC, 0);
    sleep(1);

    // SPI
    wiringPiSPISetup(0, 54000000);

    // ArtNet
    char buf[530];
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_size = sizeof(client_addr);
    
    // Creating socket file descriptor
    int sock_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_fd<0)
    {
        perror("Failed to create socket");
        return -1;
    }

    // IP and Port
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(6454);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    // Bind the socket to reciever address
    if (bind(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)    
    {
        perror("Failed to bind");
        return -1;
    }

    int nonblocking = 1;
    ioctl(sock_fd, FIONBIO, &nonblocking);

    memset(pixel, 0, sizeof(pixel));

    while(1)
    {
        // Receive data
        recvfrom(sock_fd, buf, sizeof(buf), 0, (struct sockaddr *)&client_addr, &client_addr_size);
        
        update(buf);

        if (flush)
        {
            display();
        }
    }
	
    close(sock_fd);

    return 0;
}
