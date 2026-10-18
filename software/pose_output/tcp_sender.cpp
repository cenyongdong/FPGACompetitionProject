#include "tcp_sender.hpp"
#include <algorithm>
#include <chrono>
#include <stdexcept>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#endif

namespace pose::output {
    using Clock = std::chrono::steady_clock;
    struct TcpSender::Impl {
#ifdef _WIN32
        SOCKET socket = INVALID_SOCKET;
        bool winsock = false;
        static bool waiting() { auto e = WSAGetLastError(); return e == WSAEWOULDBLOCK || e == WSAEINPROGRESS || e == WSAEINTR; }
#else
        int socket = -1;
        static bool waiting() { return errno == EWOULDBLOCK || errno == EAGAIN || errno == EINPROGRESS || errno == EINTR; }
#endif
        unsigned timeout;
        explicit Impl(unsigned ms) : timeout(ms) {}
        ~Impl() {
#ifdef _WIN32
            if (socket != INVALID_SOCKET) closesocket(socket);
            if (winsock) WSACleanup();
#else
            if (socket >= 0) ::close(socket);
#endif
        }
        void writable(Clock::time_point deadline) {
            for (;;) {
                auto us = std::chrono::duration_cast<std::chrono::microseconds>(deadline - Clock::now()).count();
                if (us <= 0) throw std::runtime_error("TCP send/connect deadline exceeded; no retry");
                timeval tv { static_cast<long>(us / 1000000), static_cast<long>(us % 1000000) };
                fd_set set;
                FD_ZERO(&set); FD_SET(socket, &set);
                int n = select(static_cast<int>(socket + 1), nullptr, &set, nullptr, &tv);
                if (n > 0) return;
                if (n < 0 && waiting()) continue;
                throw std::runtime_error("TCP not writable; no retry");
            }
        }
    };
    TcpSender::TcpSender(const std::string& ipv4, std::uint16_t port, unsigned ms) : impl_(new Impl(ms)) {
        if (!port || !ms || ms > 30000) throw std::runtime_error("Invalid TCP options");
#ifdef _WIN32
        WSADATA data;
        if (WSAStartup(MAKEWORD(2, 2), &data)) throw std::runtime_error("WSAStartup failed");
        impl_->winsock = true;
#endif
        sockaddr_in address {};
        address.sin_family = AF_INET; address.sin_port = htons(port);
        if (inet_pton(AF_INET, ipv4.c_str(), &address.sin_addr) != 1) throw std::runtime_error("Expected numeric IPv4");
        impl_->socket = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
#ifdef _WIN32
        if (impl_->socket == INVALID_SOCKET) throw std::runtime_error("socket failed");
        u_long mode = 1;
        if (ioctlsocket(impl_->socket, FIONBIO, &mode)) throw std::runtime_error("Nonblocking socket failed");
#else
        if (impl_->socket < 0 || fcntl(impl_->socket, F_SETFL, O_NONBLOCK) < 0) throw std::runtime_error("Nonblocking socket failed");
#endif
        if (connect(impl_->socket, reinterpret_cast<sockaddr*>(&address), sizeof(address)) != 0) {
            if (!Impl::waiting()) throw std::runtime_error("TCP connect failed; no retry");
            impl_->writable(Clock::now() + std::chrono::milliseconds(ms));
            int error = 0;
#ifdef _WIN32
            int bytes = sizeof(error);
            int rc = getsockopt(impl_->socket, SOL_SOCKET, SO_ERROR, reinterpret_cast<char*>(&error), &bytes);
#else
            socklen_t bytes = sizeof(error);
            int rc = getsockopt(impl_->socket, SOL_SOCKET, SO_ERROR, &error, &bytes);
#endif
            if (rc || error) throw std::runtime_error("TCP connection refused; no retry");
        }
    }
    TcpSender::~TcpSender() = default;
    void TcpSender::send(const Frame& frame, unsigned fragment) {
        if (!fragment || fragment > record_bytes) throw std::runtime_error("Invalid fragment size");
        const auto bytes = encode(frame);
        auto deadline = Clock::now() + std::chrono::milliseconds(impl_->timeout);
        std::size_t offset = 0;
        while (offset < bytes.size()) {
            impl_->writable(deadline);
            auto count = std::min<std::size_t>(fragment, bytes.size() - offset);
#ifdef _WIN32
            auto n = ::send(impl_->socket, reinterpret_cast<const char*>(bytes.data() + offset), static_cast<int>(count), 0);
#else
            auto n = ::send(impl_->socket, bytes.data() + offset, count, MSG_NOSIGNAL);
#endif
            if (n < 0 && Impl::waiting()) continue;
            if (n <= 0) throw std::runtime_error("TCP send failed; no retry");
            offset += static_cast<std::size_t>(n);
        }
    }
}
