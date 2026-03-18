import mysql.connector


def main() -> None:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="12345678",
    )
    cursor = conn.cursor()
    cursor.execute("CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '12345678'")
    cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION")
    cursor.execute("FLUSH PRIVILEGES")
    conn.commit()
    cursor.close()
    conn.close()
    print("grants_applied")


if __name__ == "__main__":
    main()
