#pragma once
#include <arpa/inet.h>
#include <cerrno>
#include <chrono>
#include <cstring>
#include <netinet/tcp.h>
#include <stdexcept>
#include <sys/socket.h>
#include <unistd.h>

namespace demo_v1 {
inline uint64_t now_ns() {
	return std::chrono::duration_cast<std::chrono::nanoseconds>(
		std::chrono::steady_clock::now().time_since_epoch())
		.count();
}

struct Socket {
	int fd = -1;
	Socket() = default;

	explicit Socket(int n) : fd(n) {
		if (n < 0)
			throw std::runtime_error("socket failed");
	}

	Socket(const Socket&) = delete;

	~Socket() {
		if (fd >= 0)
			::close(fd);
	}

	void stop() {
		if (fd >= 0)
			::shutdown(fd, SHUT_RDWR);
	}

	void timeout(int seconds) {
		timeval t{seconds, 0};
		int one = 1;
		if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &t, sizeof(t)) ||
			setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &t, sizeof(t)) ||
			setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one)))
			throw std::runtime_error("Socket option failed");
	}
};

inline void read_exact(int fd, unsigned char* p, size_t bytes) {
	while (bytes) {
		const auto n = recv(fd, p, bytes, 0);
		if (n < 0 && errno == EINTR)
			continue;
		if (n <= 0)
			throw std::runtime_error("Truncated/idle CSI connection");
		p += n;
		bytes -= size_t(n);
	}
}

inline void send_exact(int fd, const unsigned char* p, size_t bytes) {
	while (bytes) {
		const auto n = ::send(fd, p, bytes, MSG_NOSIGNAL);
		if (n < 0 && errno == EINTR)
			continue;
		if (n <= 0)
			throw std::runtime_error("Result connection failed; no retry");
		p += n;
		bytes -= size_t(n);
	}
}

inline void listen_on(int fd, uint16_t port) {
	sockaddr_in address{};
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = htonl(INADDR_ANY);
	address.sin_port = htons(port);
	if (bind(fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) || listen(fd, 1))
		throw std::runtime_error("CSI listener bind failed");
}

inline void connect_result(int fd) {
	sockaddr_in address{};
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	address.sin_port = htons(39381);
	if (connect(fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)))
		throw std::runtime_error("Result SSH reverse tunnel not ready");
}
}
