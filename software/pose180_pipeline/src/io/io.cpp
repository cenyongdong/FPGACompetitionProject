#include "io.hpp"
#include <arpa/inet.h>
#include <fcntl.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#include <stdexcept>
#include <future>

namespace pose180_demo {
namespace {
struct Fd {
	int fd = -1;

	~Fd() {
		close();
	}

	void close() {
		if (fd >= 0)
			::close(fd);
		fd = -1;
	}
};

int listen(const std::string& bind, unsigned port) {
	if (!port)
		return -1;
	int fd = ::socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
	if (fd < 0)
		throw std::runtime_error("socket creation failed");
	int one = 1;
	::setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
	sockaddr_in addr{};
	addr.sin_family = AF_INET;
	addr.sin_port = htons(port);
	if (inet_pton(AF_INET, bind.c_str(), &addr.sin_addr) != 1 ||
		::bind(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) || ::listen(fd, 2)) {
		::close(fd);
		throw std::runtime_error("Cannot bind resident listener");
	}
	return fd;
}

bool dead(ssize_t n) {
	return n == 0 || (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR);
}
}

Io::Io(Shared& s, const std::string& bind, unsigned input, unsigned result, unsigned status,
	std::uint64_t session, bool mock, bool hdmi, unsigned view)
	: shared_(s) {
	std::promise<void> ready;
	auto started = ready.get_future();
	thread_ = std::thread(
		[&, bind, input, result, status, session, mock, hdmi, view, ready = std::move(ready)]() mutable {
			bool announced = false;
			try {
				Fd li{listen(bind, input)}, lo{listen(bind, result)}, ls{listen(bind, status)}, in, out;
				Fd lv{listen(bind, view)}, viewer;
				std::string view_bytes;
				std::size_t view_sent = 0;
				std::uint64_t view_begin = 0;
				std::array<unsigned char, pp::input_bytes> bytes{};
				Record sending{};
				std::size_t used = 0, sent = 0;
				bool active = false;
				std::uint64_t last_frame = 0, epoch = session;
				std::uint64_t input_progress = 0, send_begin = 0;
				ready.set_value();
				announced = true;
				while (!s.stop) {
					pollfd fds[] = {{li.fd, POLLIN, 0}, {lo.fd, POLLIN, 0}, {ls.fd, POLLIN, 0},
						{in.fd, POLLIN, 0}, {out.fd, short(active ? POLLOUT : 0), 0}, {lv.fd, POLLIN, 0},
						{viewer.fd, short(view_bytes.empty() ? 0 : POLLOUT), 0}};
					::poll(fds, 7, 10);
					if (fds[5].revents & POLLIN) {
						int fd = ::accept4(lv.fd, nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC);
						if (fd >= 0) {
							if (viewer.fd >= 0)
								::close(fd);
							else {
								int capacity = 16384;
								::setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &capacity, sizeof(capacity));
								viewer.fd = fd;
								view_bytes.clear();
								view_sent = 0;
								s.presentation.clear();
							}
						}
					}
					if (viewer.fd >= 0 && view_bytes.empty() && s.presentation.take(view_bytes)) {
						view_sent = 0;
						view_begin = now_ns();
					}
					if (viewer.fd >= 0 && !view_bytes.empty()) {
						auto n = ::send(viewer.fd, view_bytes.data() + view_sent,
							view_bytes.size() - view_sent, MSG_NOSIGNAL | MSG_DONTWAIT);
						if (n > 0) {
							view_sent += std::size_t(n);
							if (view_sent == view_bytes.size()) {
								view_bytes.clear();
								++s.stats.view_sent;
							}
						}
						if (dead(n) || (!view_bytes.empty() && now_ns() - view_begin > 500000000ull)) {
							viewer.close();
							view_bytes.clear();
							++s.stats.view_dropped;
						}
					}
					if (viewer.fd >= 0 && (fds[6].revents & (POLLHUP | POLLERR))) {
						viewer.close();
						view_bytes.clear();
					}
					if (viewer.fd < 0) {
						std::string unused;
						if (s.presentation.take(unused))
							++s.stats.view_dropped;
					}
					if (fds[0].revents & POLLIN) {
						int fd = ::accept4(li.fd, nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC);
						if (fd >= 0) {
							if (in.fd >= 0)
								::close(fd); // An extra client cannot evict a live owner.
							else {
								in.fd = fd;
								used = 0;
								last_frame = 0;
								input_progress = now_ns();
								s.input.clear();
								++epoch;
								++s.stats.reconnects;
								s.stats.input_epoch = epoch;
								s.stats.input_connected = true;
							}
						}
					}
					if (fds[1].revents & POLLIN) {
						int fd = ::accept4(lo.fd, nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC);
						if (fd >= 0) {
							if (out.fd >= 0)
								::close(fd);
							else {
								out.fd = fd;
								int capacity = 131072;
								::setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &capacity, sizeof(capacity));
								active = false;
								sent = 0;
								s.output.clear();
								s.stats.pc_connected = true;
							}
						}
					}
					if (fds[2].revents & POLLIN) {
						Fd client{::accept4(ls.fd, nullptr, nullptr, SOCK_NONBLOCK | SOCK_CLOEXEC)};
						if (client.fd >= 0) {
							auto text = s.stats.json(mock, hdmi);
							::send(client.fd, text.data(), text.size(), MSG_NOSIGNAL);
						}
					}
					if (in.fd >= 0 && (fds[3].revents & (POLLIN | POLLHUP | POLLERR))) {
						const auto n = ::recv(in.fd, bytes.data() + used, bytes.size() - used, 0);
						if (dead(n)) {
							in.close();
							used = 0;
							s.input.clear();
							s.stats.input_connected = false;
						} else if (n > 0) {
							used += n;
							if (used == bytes.size()) {
								used = 0;
								try {
									Input value;
									pp::decode_input(bytes, value.window);
									if (!value.window.source_time_ns || value.window.frame_id <= last_frame)
										throw std::runtime_error("Input order invalid");
									last_frame = value.window.frame_id;
									value.epoch = epoch;
									value.arrived = now_ns();
									input_progress = value.arrived;
									accept_input(s, value);
								} catch (...) {
									++s.stats.malformed;
									in.close();
									s.input.clear();
									s.stats.input_connected = false;
								}
							}
						}
					}
					// Close stalled framing to discard kernel backlog before a new epoch.
					if (in.fd >= 0 && now_ns() - input_progress > 2000000000ull) {
						in.close();
						used = 0;
						s.input.clear();
						s.stats.input_connected = false;
					}
					if (!active && out.fd >= 0 && s.output.take(sending)) {
						active = true;
						sent = 0;
						send_begin = now_ns();
					}
					if (active && out.fd >= 0) {
						const auto n = ::send(out.fd, sending.data() + sent, sending.size() - sent,
							MSG_NOSIGNAL | MSG_DONTWAIT);
						if (n > 0) {
							sent += n;
							if (sent == sending.size()) {
								active = false;
								++s.stats.pc_sent;
							}
						}
						if (dead(n) || (active && now_ns() - send_begin > 500000000ull)) {
							out.close();
							active = false;
							s.stats.pc_connected = false;
							++s.stats.pc_dropped;
						}
					}
					if (out.fd >= 0 && (fds[4].revents & (POLLHUP | POLLERR))) {
						out.close();
						active = false;
						s.stats.pc_connected = false;
					}
					if (out.fd < 0) {
						Record unused;
						if (s.output.take(unused))
							++s.stats.pc_dropped;
					}
				}
			} catch (...) {
				if (!announced)
					ready.set_exception(std::current_exception());
				else
					s.stats.isolated = true;
			}
		});
	try {
		started.get();
	} catch (...) {
		thread_.join();
		throw;
	}
}

Io::~Io() {
	shared_.stop = true;
	if (thread_.joinable())
		thread_.join();
}
}
