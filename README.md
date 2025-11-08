# 🌐 HTTP Proxy Caching & Network Analysis

> **Course Project – Computer Networks (Ariel University)**  
> Implemented a multi-component client–proxy–server system in Python, demonstrating HTTP request handling, caching, and persistent connections.  
> Includes full packet-level analysis with **Wireshark** and theoretical performance evaluation of HTTP and P2P architectures.

---

## 📘 Overview
This project simulates a **real-world network communication system** with a **Client**, **Proxy**, and **Server**, written in Python using **socket programming**.  
The proxy acts as an intermediary that caches responses to reduce redundant requests and improve efficiency.

The assignment also includes **Wireshark network analysis** and **theoretical calculations** comparing:
- HTTP Non-Persistent connections  
- HTTP Persistent connections  
- HTTP Persistent with Pipelining  
- P2P vs. centralized server distribution models

---

## ⚙️ Architecture
Client ⇄ Proxy ⇄ Server
            ↳ Caching Layer


### Components
- **Server:**  
  Handles client requests, processes expressions, and sends responses. Supports graceful shutdown and connection handling.
  
- **Proxy:**  
  Acts as a middle layer between client and server.  
  - Caches server responses for repeated requests.  
  - Forwards new requests to the server.  
  - Implements `TIMEOUT` and termination control for clean shutdown.  
  
- **Client:**  
  Sends multiple expressions to the proxy, receives responses, and can initiate termination.  
  Supports multi-request sessions in a single connection.

---

## 🧠 Key Features
- **Socket programming (TCP/IP)** with structured request/response handling  
- **Proxy caching mechanism** to improve efficiency and reduce redundant requests  
- **Timeout and termination control** for server/proxy lifecycle management  
- **Thread management** ensuring clean connection closures  
- **Wireshark analysis** of handshakes (SYN, ACK, FIN) and packet flows  
- **Mathematical analysis** of HTTP and P2P performance:  
  - Round-Trip Time (RTT)  
  - Propagation, transmission, and processing delays  
  - File distribution latency comparison  

---

## 🧩 File Structure
http-proxy-cache/
│
├── client.py # Client-side logic: request sending and termination
├── proxy.py # Proxy server with caching and forwarding
├── server.py # Main server logic and response generation
├── HTTP_Proxy_Cache_Design_and_Analysis.pdf # Full project report (design + Wireshark analysis)
└── README.md


---

## 🧪 Running the Project

1️⃣ **Start the Server**
```bash
python server.py
```
2️⃣ Start the Proxy
```bash
python proxy.py
```
3️⃣ Run the Client
```bash
python client.py
```
4️⃣ Follow the terminal outputs
You can send multiple requests per session, view cached responses, and test termination handling.
