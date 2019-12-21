FROM centos:7
RUN echo "ip_resolve=4" >> /etc/yum.conf
RUN yum update -y && yum install -y java-1.8.0-openjdk
# 设置时区。这对于日志、调用链等功能能否在 TSF 控制台被检索到非常重要。
RUN /bin/cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo "Asia/Shanghai" > /etc/timezone
ENV workdir /app/
# 其中 provider-demo-0.0.1-SNAPSHOT.jar 来自于第一步下载并编译的程序包，需要注意这个 jar 包要和您的 dockerfile 位于同一级目录
ENV jar provider-demo/tartget/provider-demo-0.0.1-SNAPSHOT.jar
COPY ${jar} ${workdir}
WORKDIR ${workdir}
# tsf-consul-template-docker 用于文件配置功能，如不需要可注释掉该行
ADD tsf-consul-template-docker.tar.gz /root/
# JAVA_OPTS 环境变量的值为部署组的 JVM 启动参数，在运行时 bash 替换。使用 exec 以使 Java 程序可以接收 SIGTERM 信号。
CMD ["sh", "-ec", "sh /root/tsf-consul-template-docker/script/start.sh; exec java ${JAVA_OPTS} -jar ${jar}"]
# 如果不需要使用文件配置功能，改用下面的启动命令
# CMD ["sh", "-ec", "exec java ${JAVA_OPTS} -jar ${jar}"]