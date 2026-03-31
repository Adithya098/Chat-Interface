/*
 * App-wide database health monitor that polls /db_health and surfaces
 * persistent toasts while the database is unreachable.
 */
import { useEffect, useRef, useState } from "react";
import { showToast } from "../utils/toast";

export default function DbHealthPoller() {
  const [dbDown, setDbDown] = useState(false);
  const pollRef = useRef(null);
  const dbDownRef = useRef(false);

  useEffect(() => {
    dbDownRef.current = dbDown;
  }, [dbDown]);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("/db_health");
        if (!res.ok) {
          const wasDown = dbDownRef.current;
          setDbDown(true);
          if (!wasDown) {
            showToast("Database connection is down. Contact Adithya.", "error");
          }
        } else {
          if (dbDownRef.current) showToast("Database connection restored.", "success");
          setDbDown(false);
        }
      } catch {
        const wasDown = dbDownRef.current;
        setDbDown(true);
        if (!wasDown) {
          showToast("Cannot reach server. Contact Adithya.", "error");
        }
      }
    };

    check();
    pollRef.current = setInterval(check, 10000);
    return () => clearInterval(pollRef.current);
  }, []);

  return null;
}
