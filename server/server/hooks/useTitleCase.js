export function useTitleCase(str) {
	return str.replace(/\b\w/g, function (char) {
		return char.toUpperCase();
	});
}
