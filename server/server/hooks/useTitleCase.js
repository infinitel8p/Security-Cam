export function useTitleCase(str) {
	if (!str) return str;
	return str.replace(/\b\w/g, function (char) {
		return char.toUpperCase();
	});
}
