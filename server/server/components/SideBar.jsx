"use client";
import { useEffect, useRef, useState } from "react";
import { handleClickOutside } from "@/hooks/handleClickOutside";
import { FaUserCircle } from "react-icons/fa";
import NavList from "./NavList";
import Link from "next/link";

function SideBar() {
	const [isOpen, setIsOpen] = useState(false);
	const [active, setActive] = useState("");
	const ref = useRef();
	handleClickOutside(ref, () => setIsOpen(false));

	const makeActive = (link) => {
		setActive(link);
	};

	const handleClick = () => {
		setIsOpen(!isOpen);
	};

	useEffect(() => {
		setActive(window.location.pathname);
	}, []);

	return (
		<div className="bg-[var(--color-primary)] flex items-center flex-row-reverse lg:flex-col-reverse lg:items-start justify-between fixed w-full lg:w-[300px] h-[50px] lg:h-full px-3 lg:p-5 border-r-2 border-[var(--color-secondary)]">
			<button className="group lg:hidden z-20" onClick={handleClick}>
				<span
					className={`bg-[var(--color-secondary)] w-6 h-1 mb-1 duration-200 ${
						isOpen ? "hidden" : "block"
					}`}
				></span>
				<span
					className={`bg-[var(--color-secondary)] w-6 h-1 block mb-1 transform duration-200 ${
						isOpen ? "translate-y-1 rotate-45" : "translate-y-0 rotate-0"
					}`}
				></span>
				<span
					className={`bg-[var(--color-secondary)] w-6 h-1 block transform duration-200 ${
						isOpen ? "-translate-y-1 -rotate-45" : "translate-y-0 rotate-0"
					}`}
				></span>
			</button>
			<div
				ref={ref}
				className={`${
					isOpen ? "flex" : "hidden"
				} lg:flex lg:relative absolute top-0 right-0 pt-5 lg:pt-0 h-[100vh] w-[250px] lg:w-full bg-[var(--color-primary)] items-center justify-center px-10`}
			>
				<NavList state={active} makeActive={makeActive} />
			</div>
			<div>
				<Link href="/settings/color-theme" onClick={() => makeActive("/settings/color-theme")}>
					<FaUserCircle
						className={`${
							active == "/settings/color-theme"
								? "text-[var(--color-tertiary)]"
								: "text-[var(--color-secondary)]"
						}  lg:hidden`}
						size={"25px"}
					/>
					<FaUserCircle
						className={`${
							active == "/settings/color-theme"
								? "text-[var(--color-tertiary)]"
								: "text-[var(--color-secondary)]"
						}  hidden lg:block`}
						size={"32px"}
					/>
				</Link>
			</div>
		</div>
	);
}

export default SideBar;
