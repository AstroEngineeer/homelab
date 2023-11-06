#Base Bind9 Image
FROM internetsystemsconsortium/bind9:9.18

#Copy configuration files
COPY bind9-config/named.conf.options /etc/bind/
COPY bind9-config/db.xerogravity.space /etc/bind/

# Start the Name Service
CMD ["/usr/sbin/named", "-g", "-c", "/etc/bind/named.conf", "-u", "bind"]