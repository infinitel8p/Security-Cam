import { FaCircle } from "react-icons/fa";
import { FaMemory } from "react-icons/fa";
import { FaGripfire } from "react-icons/fa";

const colors = {
	good: "text-green-400",
	bad: "text-red-400",
	neutral: "text-yellow-400",
};

function StatusBar() {
	return (
		//TODO: fix responsive
		//TODO: implement data
		<div className="flex flex-row justify-between items-center gap-6 lg:flex-column text-[var(--color-text)]">
			<div className="flex items-center">
				<FaCircle className={`mr-2 ${colors.good}`} />
				<p className="hidden lg:block">DISK:</p>
				<span>0</span>%
			</div>
			<div className="flex items-center gap-1">
				<FaCircle className={`mr-2 ${colors.good}`} />
				<span>0.06</span>
				<span>0.03</span>
				<span>0.01</span>
			</div>
			<div className="flex items-center">
				<FaMemory className={`mr-2 ${colors.neutral}`} />
				<span>5.1</span>%
			</div>
			<div className="flex items-center">
				<FaGripfire className={`mr-2 ${colors.bad}`} />
				<span>54.0</span>°C
			</div>
		</div>
	);
}

export default StatusBar;
