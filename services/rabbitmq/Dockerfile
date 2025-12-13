FROM rabbitmq:3.13

# Define environment variables.
ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

COPY init.sh /init.sh
RUN chmod +x /init.sh

# Define default command
CMD ["/init.sh"]
