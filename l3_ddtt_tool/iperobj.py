# pylint: disable=C0301,R0913,R1723,R0912,R0915,R0904,W0612,W0719,C0103
# -*- coding: utf-8 -*-
"""
:author: YOUR_NAME
:author: YOUR_NAME
:contact: YOUR_EMAIL
"""
import time
import paramiko
from paramiko import SSHClient


class SSHClient_NOAUTH(SSHClient):
    def _auth(self, username, *args):
        return self._transport.auth_none(username)


class IPERF_OBJ:
    def __init__(self, ip_address, user="TEST_USER", passwd="YOUR_SECRET", port=22):
        self.hostname = ip_address
        self.port = port
        self.iperf_data = []
        self.fail_count = 0
        self.user = user
        self.passwd = passwd
        self.channel = None
        self._establish_connection()


    def _establish_connection(self):
        while True:
            if self.fail_count >= 100:
                print(f"Too many failures to establish SSH connection to server {self.hostname}.")
                exit(0)
            try:
                print(f"Try to establish SSH connection to server {self.hostname}")
                self.s = paramiko.SSHClient()
                self.s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.s.connect(hostname=self.hostname, port=self.port, username=self.user, password=self.passwd)
                self.channel = self.s.invoke_shell(term='xterm')
                break
            except Exception as e:
                self.fail_count += 1
                print(f"SSH connection to server {self.hostname} failed! - failed count: {self.fail_count}")
                print(f"Error: {e}")
                print("Will try again in 30 seconds.")
                time.sleep(30)

    def __del__(self):
        try:
            self.s.close()
        except:
            pass

    def close_connection(self):
        self.s.close()

    def run_iperf_for_download(self, ue_ip, port, bitrate, duration, output_logname, iperf_ver, queue=None):
        """

        :param ue_ip:
        :param port:
        :param bitrate:
        :param duration:
        :param output_logname:
        :param iperf_ver:
        :param queue:
        :return:
        """
        command = f'nohup iperf -c {ue_ip} -u -l 1360 -p {port} -b {bitrate}M -t {duration} > {output_logname} &\n'
        if 'V3' in iperf_ver.upper():
            command = f'iperf3 -c {ue_ip} -u -l 1360 -p {port} -b {bitrate}M -t {duration} > {output_logname} &\n'

        # print(f"IPERF COMMAND: {command.strip()}")
        try:
            self.channel.send(command)

            if queue:
                unique_marker = "PID_MARKER"
                self.channel.send(f'echo {unique_marker} $!\n')
                # 等待输出
                time.sleep(1)
                output = ''
                while not self.channel.recv_ready():
                    # 等待片刻再检查
                    time.sleep(0.1)
                while self.channel.recv_ready():
                    output += self.channel.recv(1024).decode()
                print("Output: ", output)

                start_index = output.find(unique_marker)
                if start_index != -1:
                    pid_line = output[start_index:].strip()
                    _, pid = pid_line.split()
                    pid = int(pid)
                    queue.put(pid)
                else:
                    print("Unable to find PID marker")
        except Exception as e:
            print(e)
            raise

    @staticmethod
    def print_log(msg):
        print(msg)

    def get_iperf_pid(self, ue_ip, profile, queue):
        ps_command = f"ps aux | grep -v grep | grep -v bash | grep 'iperf' | grep '{ue_ip}' | awk '{{print $2}}'"
        stdin, stdout, stderr = self.s.exec_command(ps_command)
        pid = stdout.read().decode().strip()
        queue.put((pid, ue_ip, *profile))

    def get_iperf_pids(self, ue_ips, profile, queue):
        """
        Demand changes, 2Ue required
        :param ue_ips:
        :param profile:
        :param queue:
        :return:
        """
        pids = []
        for ue_ip in ue_ips:
            ps_command = f"ps aux | grep -v grep | grep -v bash | grep 'iperf' | grep '{ue_ip}' | awk '{{print $2}}'"
            stdin, stdout, stderr = self.s.exec_command(ps_command)
            pid = stdout.read().decode().strip()
            pids.append(pid)
        queue.put((str(tuple(pids)), str(ue_ips), *profile))


    def channel_cmd(self, cmd):
        """

        :param cmd:
        :return:
        """
        if self.channel:
            try:
                self.channel.send(cmd + '\n')
            except Exception as exp:
                # print('CMD send errors: %s' % exp)
                return None
            time.sleep(1)
            try:
                res = self.channel.recv(1024 * 100000).decode('utf-8')
            except Exception as exp:
                print('CMD receive errors: %s' % exp)
                return None

            begin_pos = res.find('\r\n')
            end_pos = res.rfind('\r\n')
            if begin_pos == end_pos:
                result = ''
            else:
                result = res[begin_pos + 2:end_pos]

            print('The ssh command output: %s' % result)
        else:
            print('SSH channel is not established.')
            res = None

        return res
